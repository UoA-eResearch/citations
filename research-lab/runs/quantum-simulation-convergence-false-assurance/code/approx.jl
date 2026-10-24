# BP-PEPS (TensorNetworkQuantumSimulator.jl) and Pauli propagation (PauliPropagation.jl) ladders (plan section 2).
# usage: julia --project=/mnt/qsim/env approx.jl INSTANCES.json OUT.json METHOD SETTINGS [SHARD NSHARDS]
#   METHOD = bp | pp ; SETTINGS = comma list of chi (bp) or min_abs_coeff (pp), coarse to fine
# Each run is applied layer by layer; a run exceeding TLIMIT seconds (default 900, the plan's 15-minute rule) or
# PP_MAXTERMS Pauli strings is abandoned (value NaN, status "timeout"/"terms") and finer settings for that instance skipped.
# Conventions match code/instances.py: RX(t) = exp(-i t X/2), RZ(t) = exp(-i t Z/2), RZZ(t) = exp(-i t ZZ/2).
using JSON3, TensorNetworkQuantumSimulator, PauliPropagation, NamedGraphs, Graphs

const TLIMIT = parse(Float64, get(ENV, "TLIMIT", "900"))
const PP_MAXTERMS = parse(Int, get(ENV, "PP_MAXTERMS", "200000000"))

# layers of (name, qubits, angle); the flat gate order matches code/instances.py gates()
function layers(ins)
    n = ins.n; p = ins.params; L = Vector{Tuple{String, Vector{Int}, Float64}}[]
    if ins.family == "F"
        for _ in 1:p.cycles, m in 0:2
            g = Tuple{String, Vector{Int}, Float64}[]
            append!(g, [("RX", [q], p.tx / 3) for q in 0:n-1])
            append!(g, [("RZ", [q], p.tz / 3) for q in 0:n-1])
            append!(g, [("RZZ", [e[1], e[2]], p.tzz) for e in ins.edges if e[3] == m])
            push!(L, g)
        end
    else
        for _ in 1:p.layers
            g = Tuple{String, Vector{Int}, Float64}[]
            append!(g, [("RX", [q], p.theta) for q in 0:n-1])
            for m in 0:2
                append!(g, [("RZZ", [e[1], e[2]], -pi / 2) for e in ins.edges if e[3] == m])
            end
            push!(L, g)
        end
    end
    return L
end

function run_bp(ins, chi)
    n = ins.n
    g = NamedGraph(collect(1:n))
    for e in ins.edges
        Graphs.add_edge!(g, e[1] + 1 => e[2] + 1)
    end
    psi0 = tensornetworkstate(ComplexF64, v -> "↑", g, "S=1/2")
    bpc = BeliefPropagationCache(psi0)
    t0 = time(); maxerr = 0.0; sumerr = 0.0
    for layer in layers(ins)
        tn = [(name == "RX" ? "Rx" : name == "RZ" ? "Rz" : "Rzz", [q + 1 for q in qs], t) for (name, qs, t) in layer]
        bpc, errs = apply_gates(tn, bpc; apply_kwargs = (maxdim = chi, cutoff = 1.0e-10, normalize_tensors = false), verbose = false)
        maxerr = max(maxerr, maximum(errs; init = 0.0)); sumerr += sum(errs)
        time() - t0 > TLIMIT && return NaN, Dict("max_gate_err" => maxerr, "sum_gate_err" => sumerr), "timeout"
    end
    mag = sum(real(expect(bpc, ("Z", [v]))) for v in 1:n) / n
    return mag, Dict("max_gate_err" => maxerr, "sum_gate_err" => sumerr), "ok"
end

function run_pp(ins, eps)
    n = ins.n
    ps = PauliSum(n)
    for q in 1:n
        add!(ps, :Z, q, 1.0 / n)
    end
    t0 = time(); maxterms = length(ps)
    # Heisenberg picture: the last layer acts first; propagate() applies each chunk's gates in reverse
    for layer in reverse(layers(ins))
        circ = Gate[]; th = Float64[]
        for (name, qs, t) in layer
            push!(circ, name == "RX" ? PauliRotation([:X], [qs[1] + 1]) : name == "RZ" ? PauliRotation([:Z], [qs[1] + 1]) :
                        PauliRotation([:Z, :Z], [qs[1] + 1, qs[2] + 1]))
            push!(th, t)
        end
        ps = propagate(circ, ps, th; min_abs_coeff = eps)
        maxterms = max(maxterms, length(ps))
        time() - t0 > TLIMIT && return NaN, Dict("max_terms" => maxterms), "timeout"
        maxterms > PP_MAXTERMS && return NaN, Dict("max_terms" => maxterms), "terms"
    end
    return overlapwithzero(ps), Dict("max_terms" => maxterms, "final_terms" => length(ps)), "ok"
end

function main()
    I = JSON3.read(read(ARGS[1], String))
    method = ARGS[3]
    settings = method == "bp" ? parse.(Int, split(ARGS[4], ",")) : parse.(Float64, split(ARGS[4], ","))
    shard = length(ARGS) >= 6 ? parse(Int, ARGS[5]) : 0
    nsh = length(ARGS) >= 6 ? parse(Int, ARGS[6]) : 1
    out = Dict{String, Any}[]
    for (k, ins) in enumerate(I)
        (k - 1) % nsh == shard || continue
        stop = false
        for s in settings
            if stop
                push!(out, Dict("id" => ins.id, "method" => method, "setting" => s, "value" => NaN, "status" => "skipped"))
                continue
            end
            t = @elapsed begin
                val, diag, status = method == "bp" ? run_bp(ins, s) : run_pp(ins, s)
            end
            push!(out, Dict("id" => ins.id, "method" => method, "setting" => s, "value" => val, "diag" => diag,
                            "status" => status, "secs" => t))
            stop = status != "ok"
            open(ARGS[2], "w") do io
                JSON3.write(io, out; allow_inf = true)
            end
            GC.gc()
        end
    end
end

main()
