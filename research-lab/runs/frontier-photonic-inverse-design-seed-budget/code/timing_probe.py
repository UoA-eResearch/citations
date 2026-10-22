"""Timing probe before preregistration: seconds per optimizer step (one forward + one adjoint solve) on each
candidate challenge, single process, CPU. Prints timings only; no metric value is recorded or printed."""
import json
import sys
import time

import jax
import invrs_gym
import invrs_opt

jax.config.update("jax_enable_x64", True)
NAMES = sys.argv[1:] or ["ceviche_lightweight_waveguide_bend", "ceviche_waveguide_bend", "ceviche_mode_converter",
                         "ceviche_beam_splitter", "ceviche_power_splitter", "ceviche_wdm", "metagrating"]
out = {}
for name in NAMES:
    try:
        ch = getattr(invrs_gym.challenges, name)()
        params = ch.component.init(jax.random.PRNGKey(0))
        opt = invrs_opt.lbfgsb()
        state = opt.init(params)

        def loss_fn(p):
            response, aux = ch.component.response(p)
            return ch.loss(response), (response, aux)

        vg = jax.value_and_grad(loss_fn, has_aux=True)
        t = []
        for i in range(4):
            t0 = time.time()
            params = opt.params(state)
            (value, (response, aux)), grad = vg(params)
            state = opt.update(grad=grad, value=value, params=params, state=state)
            jax.block_until_ready(state)
            t.append(time.time() - t0)
        out[name] = {"first_step_s": round(t[0], 2), "steady_step_s": round(sum(t[1:]) / 3, 3)}
    except Exception as e:
        out[name] = {"error": repr(e)[:200]}
    print(name, out[name], flush=True)
json.dump(out, open("results/tables/timing_probe.json", "w"), indent=1)
