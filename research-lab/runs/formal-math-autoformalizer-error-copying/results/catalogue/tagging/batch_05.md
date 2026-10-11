# Tagging batch 05 (40 items)

## t059

**Informal statement**

For every real number $x_1$, construct the sequence $x_1,x_2,\ldots$ by setting $x_{n+1}=x_n \left(x_n + \frac{1}{n}\right)$ for each $n \geq 1$.  Prove that there exists exactly one value of $x_1$ for which $0<x_n<x_{n+1}<1$ for every $n$.

**Formal statement A**

```lean
theorem X
  (f : ℕ → ℝ → ℝ)
  (h₀ : ∀ x, f 1 x = x)
  (h₁ : ∀ n x, 0 < n → f (n + 1) x = f n x * (f n x + 1 / n)) :
  ∃! a, ∀ n, 0 < n → 0 < f n a ∧ f n a < f (n + 1) a ∧ f (n + 1) a < 1
```

**Formal statement B**

```lean
theorem X (f : ℕ → NNReal → ℝ) (h₀ : ∀ x, f 1 x = x)
    (h₁ : ∀ x n, f (n + 1) x = f n x * (f n x + 1 / n)) :
    ∃! a, ∀ n, 0 < n → 0 < f n a ∧ f n a < f (n + 1) a ∧ f (n + 1) a < 1
```

## t270

**Informal statement**

Prove that the Cauchy product of two absolutely convergent series converges absolutely.

**Formal statement A**

```lean
theorem X
  (a b : ℕ → ℝ)
  (ha : ∃ y, (Tendsto (λ n => (∑ i in (range n), |a i|)) atTop (𝓝 y)))
  (hb : ∃ y, (Tendsto (λ n => (∑ i in (range n), |b i|)) atTop (𝓝 y))) :
  ∃ y, (Tendsto (λ n => (∑ i in (range n),
  |λ i => (∑ j in range (i + 1), a j * b (i - j))|)) atTop (𝓝 y))
```

**Formal statement B**

```lean
theorem X
  (a b : ℕ → ℝ)
  (ha : ∃ y, (Tendsto (λ n => (∑ i in (range n), |a i|)) atTop (𝓝 y)))
  (hb : ∃ y, (Tendsto (λ n => (∑ i in (range n), |b i|)) atTop (𝓝 y))) :
  ∃ y, (Tendsto (λ n => (∑ i in (range n),
  λ i => (∑ j in range (i + 1), a j * b (i - j)))) atTop (𝓝 y))
```

## t251

**Informal statement**

Show that if $X$ is regular, every pair of points of $X$ have neighborhoods whose closures are disjoint.

**Formal statement A**

```lean
theorem X {X : Type*} [TopologicalSpace X]
  (hX : RegularSpace X) (x y : X) (hxy : x ≠ y) :
  ∃ (U V : Set X), IsOpen U ∧ IsOpen V ∧ x ∈ U ∧ y ∈ V ∧ closure U ∩ closure V = ∅
```

**Formal statement B**

```lean
theorem X {X : Type*} [TopologicalSpace X]
  (hX : RegularSpace X) (x y : X) :
  ∃ (U V : Set X), IsOpen U ∧ IsOpen V ∧ x ∈ U ∧ y ∈ V ∧ closure U ∩ closure V = ∅
```

## t007

**Informal statement**

Find the positive solution to
<center>$\frac 1{x^2-10x-29}+\frac1{x^2-10x-45}-\frac 2{x^2-10x-69}=0$</center> Show that it is 013.

**Formal statement A**

```lean
theorem X (x : ℝ) (h₀ : 0 < x) (h₁ : x ^ 2 - 10 * x - 29 ≠ 0)
    (h₂ : x ^ 2 - 10 * x - 45 ≠ 0) (h₃ : x ^ 2 - 10 * x - 69 ≠ 0)
    (h₄ : 1 / (x ^ 2 - 10 * x - 29) + 1 / (x ^ 2 - 10 * x - 45) - 2 / (x ^ 2 - 10 * x - 69) = 0) :
    x = 13
```

**Formal statement B**

```lean
theorem X (x : ℝ) (h₀ : 0 < x) 
  (h₄ : 1 / (x ^ 2 - 10 * x - 29) + 1 / (x ^ 2 - 10 * x - 45) - 2 / (x ^ 2 - 10 * x - 69) = 0) :
  x = 13
```

## t023

**Informal statement**

The first three terms of an arithmetic sequence are $2x - 3$, $5x - 11$, and $3x + 1$ respectively. The $n$th term of the sequence is $2009$. What is $n$?

$\textbf{(A)}\ 255 \qquad \textbf{(B)}\ 502 \qquad \textbf{(C)}\ 1004 \qquad \textbf{(D)}\ 1506 \qquad \textbf{(E)}\ 8037$ Show that it is 502.

**Formal statement A**

```lean
theorem X (x : ℝ) (n : ℕ) (a : ℕ → ℝ)
    (h₁ : ∀ m, a (m + 1) - a m = a (m + 2) - a (m + 1)) (h₂ : a 1 = 2 * x - 3)
    (h₃ : a 2 = 5 * x - 11) (h₄ : a 3 = 3 * x + 1) (h₅ : a n = 2009) : n = 502
```

**Formal statement B**

```lean
theorem X (x : ℝ) (n : ℕ+) (a : ℕ+ → ℝ)
  (h₁ : ∀ m, a (m + 1) - a m = a (m + 2) - a (m + 1)) (h₂ : a 1 = 2 * x - 3)
  (h₃ : a 2 = 5 * x - 11) (h₄ : a 3 = 3 * x + 1) (h₅ : a n = 2009) : n = 502
```

## t130

**Informal statement**

The four-digit number $\underline{374n}$ is divisible by 18. Find the units digit $n$. Show that it is 4.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : n ≤ 9) (h₁ : 18 ∣ 374 * 10 + n) : n = 4
```

**Formal statement B**

```lean
theorem X
  (n x : ℕ)
  (h₀ : Nat.digits 10 x = [n, 4, 7, 3])
  (h₁ : 18 ∣ x) : n = 4
```

## t148

**Informal statement**

Let $r$ be the remainder when $1342$ is divided by $13$.

Determine the smallest positive integer that has these two properties:

$\bullet~$ It is a multiple of $1342$.

$\bullet~$ Its remainder upon being divided by $13$ is smaller than $r$. Show that it is 6710.

**Formal statement A**

```lean
theorem X (r n : ℕ) (h₀ : r = 1342 % 13) (h₁ : 0 < n) (h₂ : 1342 ∣ n)
    (h₃ : n % 13 < r) : 6710 ≤ n
```

**Formal statement B**

```lean
theorem X 
  (r n : ℕ) (h₀ : r = 1342 % 13)
  (S : Set ℕ)
  (hS: S = {x | 0 < x ∧ (∃ k:ℕ, k * 1342 = x) ∧ x % 13 < r}):
  IsLeast S 6710
```

## t284

**Informal statement**

Prove that the power series $\sum zn/n^2$ converges at every point of the unit circle.

**Formal statement A**

```lean
theorem X (z : ℂ) (hz : abs z = 1) (s : ℕ → ℂ)
    (h : s = (λ n => ∑ i in (range n), z ^ (i + 1) / (i + 1) ^ 2)) :
    ∃ y, Tendsto s atTop (𝓝 y)
```

**Formal statement B**

```lean
theorem X (z : ℂ) (hz : abs z = 1) (s : ℕ → ℂ)
    (h : s = (λ n => ∑ i in (range n), i * z / i ^ 2)) :
    ∃ y, Tendsto s atTop (𝓝 y)
```

## t098

**Informal statement**

The two positive integer solutions of the equation $x^2 - mx + n = 0$ are $k$ and $t$, where $m$ and $n$ are both prime numbers and $k > t$. What is the value of $m^n + n^m + k^t + t^k$? Show that it is 20.

**Formal statement A**

```lean
theorem X (k t m n : ℕ) (h₀ : Nat.Prime m ∧ Nat.Prime n) (h₁ : t < k)
    (h₂ : (k ^ 2 : ℤ) - m * k + n = 0) (h₃ : (t ^ 2 : ℤ) - m * t + n = 0) :
    m ^ n + n ^ m + k ^ t + t ^ k = 20
```

**Formal statement B**

```lean
theorem X (k t m n : ℕ) (f : ℕ → ℤ) (hf : f = fun (x:ℕ) ↦ ((↑x:ℤ) ^ 2 - m * x + n)) (h₀ : Nat.Prime m ∧ Nat.Prime n) (h₁ : t < k)
  (h₂ : f k = 0) (h₃ : f t = 0) :
  m ^ n + n ^ m + k ^ t + t ^ k = 20
```

## t233

**Informal statement**

Let $V$ be a vector space over an infinite field $F$. Show that $V$ cannot be the set-theoretic union of a finite number of proper subspaces of $V$.

**Formal statement A**

```lean
theorem X {F V ι: Type*} [Infinite F] [Field F]
  [AddCommGroup V] [Module F V] [Finite ι] {u : ι → Submodule F V}
  (hu : ∀ i : ι, u i ≠ ⊤) :
  (⋃ i : ι, (u i : Set V)) ≠ ⊤
```

**Formal statement B**

```lean
theorem X {F V ι: Type*} [Infinite F] [Field F]
  [AddCommGroup V] [Module F V] {u : ι → Submodule F V}
  (hu : ∀ i : ι, u i ≠ ⊤) :
  (⋃ i : ι, (u i : Set V)) ≠ ⊤
```

## t154

**Informal statement**

What is the units digit of the product of all of the odd integers between 0 and 12? Show that it is 5.

**Formal statement A**

```lean
theorem X
  (S : Finset ℕ)
  (hS : S = Finset.filter (fun x => Odd x) (Finset.range 13))
  (p : ℕ)
  (h₀: p = ∏ k ∈ S, k) :
  p % 10 = 5
```

**Formal statement B**

```lean
theorem X : (∏ k in Finset.range 6, 2 * k + 1) % 10 = 5
```

## t264

**Informal statement**

Suppose $a, b \in R^k$. Find $c \in R^k$ and $r > 0$ such that $|x-a|=2|x-b|$ if and only if $| x - c | = r$. Prove that $3c = 4b - a$ and $3r = 2 |b - a|$.

**Formal statement A**

```lean
theorem X
  (n : ℕ)
  (a b : EuclideanSpace ℝ (Fin n))
  : (∃ c r, r > 0 ∧ (∀ x, ‖x - a‖ = 2 * ‖x - b‖ ↔ ‖x - c‖ = r)) ∧
    (∀ c r, (r > 0 ∧ (∀ x, ‖x - a‖ = 2 * ‖x - b‖ ↔ ‖x - c‖ = r)) →
      (3 • c = 4 • b - a ∧ 3 * r = 2 * ‖b - a‖))
```

**Formal statement B**

```lean
theorem X
  (n : ℕ)
  (a b c x : EuclideanSpace ℝ (Fin n))
  (r : ℝ)
  (h₁ : r > 0)
  (h₂ : 3 • c = 4 • b - a)
  (h₃ : 3 * r = 2 * ‖x - b‖)
  : ‖x - a‖ = 2 * ‖x - b‖ ↔ ‖x - c‖ = r
```

## t241

**Informal statement**

Let $p$ be an odd prime. Show that $a$ is a primitive root modulo $p$ iff $a^{(p-1) / q} \not \equiv 1(p)$ for all prime divisors $q$ of $p-1$.

**Formal statement A**

```lean
theorem X {p a : ℕ} (hp : Odd p) :
  IsPrimitiveRoot a p ↔ (∀ q : ℕ, q ∣ (p-1) → q.Prime → ¬ a^(p-1) ≡ 1 [MOD p])
```

**Formal statement B**

```lean
theorem X {p : ℕ} {a : ZMod p} (hp : Odd p) (hp' : p.Prime) :
  IsPrimitiveRoot a p ↔ (∀ q : ℕ, q ∣ (p-1) → q.Prime → ¬ a^((p-1)/q) = 1)
```

## t214

**Informal statement**

Let $|G|=p q r$, where $p, q$ and $r$ are primes with $p<q<r$. Prove that $G$ has a normal Sylow subgroup for either $p, q$ or $r$.

**Formal statement A**

```lean
theorem X {p q r : ℕ} {G : Type*} [Group G]
  [Fintype G]  (hpqr : p < q ∧ q < r)
  (hpqr1 : p.Prime ∧ q.Prime ∧ r.Prime)(hG : card G = p*q*r) :
  Nonempty (Sylow p G) ∨ Nonempty (Sylow q G) ∨ Nonempty (Sylow r G)
```

**Formal statement B**

```lean
theorem X {p q r : ℕ} {G : Type*} [Group G]
  [Fintype G]  (hpqr : p < q ∧ q < r)
  (hpqr1 : p.Prime ∧ q.Prime ∧ r.Prime)(hG : card G = p*q*r) :
  (∃ (P : Sylow p G), P.Normal) ∨ (∃ (P : Sylow q G), P.Normal) ∨ (∃ (P : Sylow r G), P.Normal)
```

## t123

**Informal statement**

What is the distance between the two intersections of $y=x^2$ and $x+y=1$? Show that it is \sqrt{10}.

**Formal statement A**

```lean
theorem X (a b c d : ℝ) (h₀ : b = a ^ 2) (h₁ : a + b = 1) (h₂ : d = c ^ 2)
    (h₃ : c + d = 1) (h₄ : a ≠ c) : Real.sqrt ((a - c) ^ 2 + (b - d) ^ 2) = Real.sqrt 10
```

**Formal statement B**

```lean
theorem X
  (F G I : Set (EuclideanSpace ℝ (Fin 2)))
  (hF : F = { x | x 1 = (x 0) ^ 2})
  (hG : G = { x | x 0 + x 1 = 1})
  (hI : I = (F ∩ G))
  (A B : EuclideanSpace ℝ (Fin 2))
  (h₀ : ∀ x, x ∈ I ↔ x = A ∨ x = B) :
  dist A B = Real.sqrt 10
```

## t185

**Informal statement**

Show that $\frac{-1 + \sqrt{3}i}{2}$ is a cube root of 1 (meaning that its cube equals 1).

**Formal statement A**

```lean
theorem X :
  (⟨-1/2, Real.sqrt 3 / 2⟩ : ℂ) ^ 3 = 1
```

**Formal statement B**

```lean
theorem X :
  (⟨-1/2, Real.sqrt 3 / 2⟩ : ℂ) ^ 3 = -1
```

## t043

**Informal statement**

If $\log (xy^3) = 1$ and $\log (x^2y) = 1$, what is $\log (xy)$?

$\mathrm{(A)}\ -\frac 12 
\qquad\mathrm{(B)}\ 0 
\qquad\mathrm{(C)}\ \frac 12
\qquad\mathrm{(D)}\ \frac 35 
\qquad\mathrm{(E)}\ 1$ Show that it is \mathrm{(D)} \frac 35.

**Formal statement A**

```lean
theorem X (x y : ℝ) (h₀ : 0 < x ∧ 0 < y) (h₁ : Real.log (x * y ^ 3) = 1)
  (h₂ : Real.log (x ^ 2 * y) = 1) : Real.log (x * y) = 3 / 5
```

**Formal statement B**

```lean
theorem X (x y : ℝ) (h₁ : Real.log (x * y ^ 3) = 1)
  (h₂ : Real.log (x ^ 2 * y) = 1) : Real.log (x * y) = 3 / 5
```

## t247

**Informal statement**

Let $p: X \rightarrow Y$ be a closed continuous surjective map such that $p^{-1}(\{y\})$ is compact, for each $y \in Y$. (Such a map is called a perfect map.) Show that if $Y$ is compact, then $X$ is compact.

**Formal statement A**

```lean
theorem X {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
  (p : X → Y) (h : Function.Surjective p) (hc : Continuous p) (hp : ∀ y, IsCompact (p ⁻¹' {y}))
  (hY : CompactSpace Y) : CompactSpace X
```

**Formal statement B**

```lean
theorem X {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
  (p : X → Y) (h : Function.Surjective p) (hc : Continuous p)
  (hp : IsClosedMap p) (hp : ∀ y, IsCompact (p ⁻¹' {y}))
  (hY : CompactSpace Y) : CompactSpace X
```

## t278

**Informal statement**

Suppose $a \in R^{1}, f$ is a twice-differentiable real function on $(a, \infty)$, and $M_{0}, M_{1}, M_{2}$ are the least upper bounds of $|f(x)|,\left|f^{\prime}(x)\right|,\left|f^{\prime \prime}(x)\right|$, respectively, on $(a, \infty)$. Prove that $M_{1}^{2} \leq 4 M_{0} M_{2} .$

**Formal statement A**

```lean
theorem X {f : ℝ → ℝ} (a M0 M1 M2 : ℝ)
  (hf' : DifferentiableOn ℝ f (Set.Ici a))
  (hf'' : DifferentiableOn ℝ (deriv f) (Set.Ici a))
  (hM0 : M0 = sSup {(|f x|) | x ∈ (Set.Ici a)})
  (hM1 : M1 = sSup {(|deriv f x|) | x ∈ (Set.Ici a)})
  (hM2 : M2 = sSup {(|deriv (deriv f) x|) | x ∈ (Set.Ici a)}) :
  (M1 ^ 2) ≤ 4 * M0 * M2
```

**Formal statement B**

```lean
theorem X {f : ℝ → ℝ} (a M0 M1 M2 : ℝ)
  (hf' : DifferentiableOn ℝ f (Set.Ioi a))
  (hf'' : DifferentiableOn ℝ (deriv f) (Set.Ioi a))
  (hM0 : M0 = sSup {(|f x|) | x ∈ (Set.Ioi a)})
  (hM1 : M1 = sSup {(|deriv f x|) | x ∈ (Set.Ioi a)})
  (hM2 : M2 = sSup {(|deriv (deriv f) x|) | x ∈ (Set.Ioi a)}) :
  (M1 ^ 2) ≤ 4 * M0 * M2
```

## t047

**Informal statement**

For all integers $n \geq 9,$ the value of
$\frac{(n+2)!-(n+1)!}{n!}$is always which of the following?

$\textbf{(A) } \text{a multiple of 4} \qquad \textbf{(B) } \text{a multiple of 10} \qquad \textbf{(C) } \text{a prime number} \qquad \textbf{(D) } \text{a perfect square} \qquad \textbf{(E) } \text{a perfect cube}$ Show that it is \textbf{(D) } \text{a perfect square}.

**Formal statement A**

```lean
theorem X  (n : ℕ) (hn : 9 ≤ n) : IsSquare (((n + 2)! - (n + 1)!) / n !)
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 9 ≤ n) : ∃ x : ℕ, (x : ℝ) ^ 2 = ((n + 2)! - (n + 1)!) / n !
```

## t122

**Informal statement**

The volume of a cone is given by the formula $V = \frac{1}{3}Bh$, where $B$ is the area of the base and $h$ is the height. The area of the base of a cone is 30 square units, and its height is 6.5 units. What is the number of cubic units in its volume? Show that it is 65.

**Formal statement A**

```lean
theorem X (b h v u : ℝ) (h₁ : v = 1 / 3 * (b * h))
  (h₂ : b = 30 * u) (h₃ : h = 13 / 2 * u) : v = 65 * u
```

**Formal statement B**

```lean
theorem X (b h v : ℝ) (h₀ : 0 < b ∧ 0 < h ∧ 0 < v) (h₁ : v = 1 / 3 * (b * h))
    (h₂ : b = 30) (h₃ : h = 13 / 2) : v = 65
```

## t180

**Informal statement**

Prove that $x^3 + 6x + 12$ is irreducible in $\mathbb{Q}$.

**Formal statement A**

```lean
theorem X :
  Irreducible (12 + 6 * X + X ^ 3 : Polynomial ℚ)
```

**Formal statement B**

```lean
theorem X {F : Type*} [Field F] [Fintype F] (hF : card F = 2) :
  Irreducible (12 + 6 * X + X ^ 3 : Polynomial F)
```

## t239

**Informal statement**

Consider a prime $p$ of the form $4 t+3$. Show that $a$ is a primitive root modulo $p$ iff $-a$ has order $(p-1) / 2$.

**Formal statement A**

```lean
theorem X {p t : ℕ} (hp0 : p.Prime) (hp1 : p = 4*t + 3)
  (a : ZMod p) :
  IsPrimitiveRoot a p ↔ ((-a) ^ ((p-1)/2) = 1 ∧ ∀ (k : ℕ), k < (p-1)/2 → (-a)^k ≠ 1)
```

**Formal statement B**

```lean
theorem X {p t : ℕ} (hp0 : p.Prime) (hp1 : p = 4*t + 3)
  (a : ZMod p) :
  IsPrimitiveRoot a p ↔ ((-a) ^ ((p-1)/2) = 1 ∧ ∀ (k : ℕ), (0 < k ∧ k < (p-1)/2) → (-a)^k ≠ 1)
```

## t249

**Informal statement**

Show that if $X$ is a Hausdorff space that is locally compact at the point $x$, then for each neighborhood $U$ of $x$, there is a neighborhood $V$ of $x$ such that $\bar{V}$ is compact and $\bar{V} \subset U$.

**Formal statement A**

```lean
theorem X {X : Type*}
  [TopologicalSpace X] [T2Space X] (x : X)
  (hx : ∃ U : Set X, x ∈ U ∧ IsOpen U ∧ (∃ K : Set X, U ⊆ K ∧ IsCompact K))
  (U : Set X) (hU : IsOpen U) (hxU : x ∈ U) :
  ∃ (V : Set X), IsOpen V ∧ x ∈ V ∧ IsCompact (closure V) ∧ closure V ⊆ U
```

**Formal statement B**

```lean
theorem X {X : Type*}
  [TopologicalSpace X] [T2Space X] (x : X)
  (hx : ∃ U : Set X, x ∈ U ∧ IsOpen U ∧ (∃ K : Set X, U ⊂ K ∧ IsCompact K))
  (U : Set X) (hU : IsOpen U) (hxU : x ∈ U) :
  ∃ (V : Set X), IsOpen V ∧ x ∈ V ∧ IsCompact (closure V) ∧ closure V ⊆ U
```

## t110

**Informal statement**

If $f(x)=4x^3+1$, find $f^{-1}(33)$. Show that it is 2.

**Formal statement A**

```lean
theorem X 
  (f : ℝ → ℝ)
  (h₀: f = fun x ↦ 4 * x ^ 3 + 1) :
  f⁻¹ 33 = 2
```

**Formal statement B**

```lean
theorem X (σ : Equiv ℝ ℝ) (h₀ : ∀ x, σ.1 x = 4 * x ^ 3 + 1) : σ.2 33 = 2
```

## t092

**Informal statement**

Let $t=2s-s^2$ and $s=n^2 - 2^n+1$. What is the value of $t$ when $n=3$? Show that it is 0.

**Formal statement A**

```lean
theorem X (t s : ℝ) (n : ℤ) (h₀ : t = 2 * s - s ^ 2) (h₁ : s = n ^ 2 - 2 ^ n + 1)
  (n) (_ : n = 3) : t = 0
```

**Formal statement B**

```lean
theorem X (t s : ℝ) (n : ℤ) (h₀ : t = 2 * s - s ^ 2) (h₁ : s = n ^ 2 - 2 ^ n + 1)
  (h₂ : n = 3) :
  t = 0
```

## t027

**Informal statement**

Positive real numbers $x \neq 1$ and $y \neq 1$ satisfy $\log_2{x} = \log_y{16}$ and $xy = 64$. What is $(\log_2{\tfrac{x}{y}})^2$?

$\textbf{(A) } \frac{25}{2} \qquad\textbf{(B) } 20 \qquad\textbf{(C) } \frac{45}{2} \qquad\textbf{(D) } 25 \qquad\textbf{(E) } 32$ Show that it is \textbf{(B) } 20.

**Formal statement A**

```lean
theorem X (x y : ℝ) (h₀ : x ≠ 1 ∧ y ≠ 1)
    (h₁ : Real.log x / Real.log 2 = Real.log 16 / Real.log y) (h₂ : x * y = 64) :
    (Real.log (x / y) / Real.log 2) ^ 2 = 20
```

**Formal statement B**

```lean
theorem X
  (x y : ℝ)
  (h₀ : x ≠ 1 ∧ y ≠ 1)
  (hx₀: 0 < x)
  (hy₀: 0 < y)
  (h₁ : Real.logb 2 x = Real.logb y 16)
  (h₂ : x * y = 64) :
  (Real.logb 2 (x / y)) ^ 2 = 20
```

## t015

**Informal statement**

Let $A, M,$ and $C$ be [[nonnegative integer]]s such that $A + M + C=12$. What is the maximum value of $A \cdot M \cdot C + A \cdot M + M \cdot C + A \cdot C$?

$ \mathrm{(A) \ 62 } \qquad \mathrm{(B) \ 72 } \qquad \mathrm{(C) \ 92 } \qquad \mathrm{(D) \ 102 } \qquad \mathrm{(E) \ 112 }  $ Show that it is \text{E}.

**Formal statement A**

```lean
theorem X
  (S: Set ℕ)
  (hS: S = {x | ∃ a m c : ℕ, (x = a * m * c + a * m + m * c + a * c) ∧a + m + c = 12}) :
  IsGreatest S 112
```

**Formal statement B**

```lean
theorem X (a m c : ℕ) (h₀ : a + m + c = 12) :
    a * m * c + a * m + m * c + a * c ≤ 112
```

## t202

**Informal statement**

Show that if $G=\langle x\rangle$ is a cyclic group of order $n \geq 1$ then a subgroup $H$ is maximal if and only $H=\left\langle x^{p}\right\rangle$ for some prime $p$ dividing $n$.

**Formal statement A**

```lean
theorem X {n : ℕ+} {G : Type*} [Group G] {x : G}
  (hx : orderOf x = n) (hG : G = Subgroup.closure {x}) (H : Subgroup G) :
  (∃ p : ℕ, Prime p ∧ p ∣ n ∧ H = Subgroup.closure {x ^ p}) ↔
  (H ≠ ⊤ ∧ ∀ K : Subgroup G, H ≤ K → K = H ∨ K = ⊤)
```

**Formal statement B**

```lean
theorem X {n : ℕ} (H : AddSubgroup (ZMod n)) :
  ∃ p : (ZMod n), Prime p ∧ H = AddSubgroup.closure {p} ↔
  (H ≠ ⊤ ∧ ∀ K : AddSubgroup (ZMod n), H ≤ K → K = H ∨ K = ⊤)
```

## t211

**Informal statement**

Prove that a group of order 56 has a normal Sylow $p$-subgroup for some prime $p$ dividing its order.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (hG : card G = 56) :
  ∃ (p : ℕ) (P : Sylow p G), p.Prime ∧ (p ∣ card G) ∧ P.Normal
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (hG : card G = 56) :
  ∃ (p : ℕ) (P : Sylow p G), P.Normal
```

## t049

**Informal statement**

Prove that the fraction $\frac{21n+4}{14n+3}$ is irreducible for every natural number $n$.

**Formal statement A**

```lean
theorem X : ∀ n : ℕ, Irreducible ((21 * n + 4) / (14 * n + 3))
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) : Nat.gcd (21 * n + 4) (14 * n + 3) = 1
```

## t081

**Informal statement**

For each plumbing repair job, Mr. Wrench charges $N$ dollars for coming out to the house plus $x$ dollars per hour that he works at the house. He charged $\$97$ for a one-hour repair job and $\$265$ for a five-hour repair job. What is his charge for a two-hour repair job? Show that it is \$ 139.

**Formal statement A**

```lean
theorem X (n x : ℝ) (h₀ : n + x = 97) (h₁ : n + 5 * x = 265) : n + 2 * x = 139
```

**Formal statement B**

```lean
theorem X
  (n x : ℕ)
  (f : ℕ → ℕ)
  (h₀ : f = fun t => n + x * t)
  (h₁: f 1 = 97)
  (h₂: f 5 = 265) :
  f 2 = 139
```

## t057

**Informal statement**

Find one pair of positive integers $a,b$ such that $ab(a+b)$ is not divisible by $7$, but $(a+b)^7-a^7-b^7$ is divisible by $7^7$.

**Formal statement A**

```lean
theorem X
  (a b : ℕ)
  (h₀ : 0 < a ∧ 0 < b)
  (h₁ : ¬ 7 ∣ a * b * (a + b))
  (h₂ : (7^7) ∣ ((a + b)^7 - a^7 - b^7)) :
  19 ≤ a + b
```

**Formal statement B**

```lean
theorem X (a b : ℤ) (h₀ : 0 < a ∧ 0 < b) (h₁ : ¬7 ∣ a) (h₂ : ¬7 ∣ b) (h₃ : ¬7 ∣ a + b)
  (h₄ : 7 ^ 7 ∣ (a + b) ^ 7 - a ^ 7 - b ^ 7) : 19 ≤ a + b
```

## t020

**Informal statement**

Consider the sequence of numbers: $4,7,1,8,9,7,6,\dots$ For $n>2$, the $n$-th term of the sequence is the units digit of the sum of the two previous terms. Let $S_n$ denote the sum of the first $n$ terms of this sequence. The smallest value of $n$ for which $S_n>10,000$ is: 

$
\text{(A) }1992
\qquad
\text{(B) }1999
\qquad
\text{(C) }2001
\qquad
\text{(D) }2002
\qquad
\text{(E) }2004
$ Show that it is (B)1999.

**Formal statement A**

```lean
theorem X
  (u S : ℕ → ℕ)
  (h₀ : u 0 = 4)
  (h₁ : u 1 = 7)
  (h₂ : ∀ n ≥ 2, u n = (u (n - 2) + u (n - 1)) % 10)
  (h₃ : ∀ n, S n = ∑ k ∈ Finset.range n, u k)
  (Sn : Set ℕ)
  (h₄ : Sn = {n | S n > 10000}) :
  IsLeast Sn 1999
```

**Formal statement B**

```lean
theorem X (u : ℕ → ℕ) (h₀ : u 0 = 4) (h₁ : u 1 = 7)
    (h₂ : ∀ n ≥ 2, u (n + 2) = (u n + u (n + 1)) % 10) :
    ∀ n, (∑ k in Finset.range n, u k) > 10000 → 1999 ≤ n
```

## t177

**Informal statement**

Let $x$ and $y$ be rational numbers. Show that if $x^2 + y^2$ is an integer, then $x$ and $y$ have the same denominator.

**Formal statement A**

```lean
theorem X (x y : ℚ) (h₀ : (x ^ 2 + y ^ 2).isInt) : x.den = y.den
```

**Formal statement B**

```lean
theorem X (x y : ℚ) (h₀ : (x ^ 2 + y ^ 2).den = 1) : x.den = y.den
```

## t283

**Informal statement**

Suppose $f^{\prime}(x), g^{\prime}(x)$ exist, $g^{\prime}(x) \neq 0$, and $f(x)=g(x)=0$. Prove that $\lim _{t \rightarrow x} \frac{f(t)}{g(t)}=\frac{f^{\prime}(x)}{g^{\prime}(x)}.$

**Formal statement A**

```lean
theorem X
  {f g : ℝ → ℝ} {x : ℝ}
  (hf' : DifferentiableAt ℝ f x)
  (hg' : DifferentiableAt ℝ g x)
  (hg'_ne_0 : deriv g x ≠ 0)
  (f0 : f x = 0) (g0 : g x = 0) :
  Tendsto (λ t => f t / g t) (𝓝 x) (𝓝 (deriv f x / deriv g x))
```

**Formal statement B**

```lean
theorem X
  {f g : ℝ → ℝ} {x : ℝ}
  (hf' : DifferentiableAt ℝ f 0)
  (hg' : DifferentiableAt ℝ g 0)
  (hg'_ne_0 : deriv g 0 ≠ 0)
  (f0 : f 0 = 0) (g0 : g 0 = 0) :
  Tendsto (λ x => f x / g x) (𝓝 x) (𝓝 (deriv f x / deriv g x))
```

## t133

**Informal statement**

What is the smallest positive integer $N$ such that the value $7 + (30 \times N)$ is not a prime number? Show that it is 6.

**Formal statement A**

```lean
theorem X
  (S : Set ℕ)
  (hS: S = {n:ℕ | 0 < n ∧ ¬ Nat.Prime (7 + 30 * n)}) :
  IsLeast S 6
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : ¬Nat.Prime (7 + 30 * n)) : 6 ≤ n
```

## t102

**Informal statement**

Let $x$ be a positive number such that $2x^2 = 4x + 9.$ If $x$ can be written in simplified form as $\dfrac{a + \sqrt{b}}{c}$ such that $a,$ $b,$ and $c$ are positive integers, what is $a + b + c$? Show that it is 26.

**Formal statement A**

```lean
theorem X (x : ℝ) (a b c : ℕ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c ∧ 0 ≤ x)
    (h₁ : 2 * x ^ 2 = 4 * x + 9) (h₂ : x = (a + Real.sqrt b) / c) (h₃ : c = 2) : a + b + c = 26
```

**Formal statement B**

```lean
theorem X
  (x : ℝ) (a b c : ℕ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c ∧ 0 < x)
  (h₁ : 2 * x ^ 2 = 4 * x + 9) (h₂ : x = (a + Real.sqrt b) / c) (h₃ : ¬ ∃d:ℕ , d ^ 2 ∣ b) : a + b + c = 26
```

## t226

**Informal statement**

Let $G$ be a finite group and $\varphi$ an automorphism of $G$ such that $\varphi(x) = x^{-1}$ for more than three-fourths of the elements of $G$. Prove that $\varphi(y) = y^{-1}$ for all $y \in G$, and so $G$ is abelian.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (φ : G ≃* G) {I : Finset G} (hI : ∀ x ∈ I, φ x = x⁻¹)
  (hI1 : (0.75 : ℚ) * card G ≤ card I) :
  (∀ x : G, φ x = x⁻¹) ∧ ∀ x y : G, x*y = y*x
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (φ : G ≃* G) {I : Finset G} (hI : ∀ x ∈ I, φ x = x⁻¹)
  (hI1 : (0.75 : ℚ) * card G ≤ card I) :
  ∀ x : G, φ x = x⁻¹ ∧ ∀ x y : G, x*y = y*x
```

## t010

**Informal statement**

Given that $\sum_{k=1}^{35}\sin 5k=\tan \frac mn,$ where angles are measured in degrees, and $m_{}$ and $n_{}$ are relatively prime positive integers that satisfy $\frac mn<90,$ find $m+n.$ Show that it is 177.

**Formal statement A**

```lean
theorem X
  (m n : ℕ)
  (hm₀ : 0 < m)
  (hn₀ : 0 < n)
  (h₀ : Nat.Coprime m n)
  (h₁ : (∑ k ∈ Finset.Icc (1 : ℕ) 35, Real.sin (5 * k * Real.pi / 180)) = Real.tan ((m / n:ℝ) * Real.pi / 180))
  (h₂ : (m : ℝ) / (n : ℝ) < 90) :
  m + n = 177
```

**Formal statement B**

```lean
theorem X (m : ℚ) (h₀ : 0 < m)
    (h₁ : (∑ k in Finset.Icc (1 : ℕ) 35, Real.sin (5 * k * Real.pi / 180)) = Real.tan (m * Real.pi / 180))
    (h₂ : (m.num : ℝ) / m.den < 90) : ↑m.den + m.num = 177
```
