# Tagging batch 03 (40 items)

## t188

**Informal statement**

Suppose that $T \in \mathcal{L}(V)$ has $\operatorname{dim} V$ distinct eigenvalues and that $S \in \mathcal{L}(V)$ has the same eigenvectors as $T$ (not necessarily with the same eigenvalues). Prove that $S T=T S$.

**Formal statement A**

```lean
theorem X {F V : Type*} [AddCommGroup V] [Field F]
  [Module F V] [FiniteDimensional F V] {S T : End F V}
  (h1 : card (T.Eigenvalues) = finrank F V)
  (h2 : ∀ v : V, (∃ c : F, v ∈ eigenspace S c) ↔ (∃ c : F, v ∈ eigenspace T c)) :
  S * T = T * S
```

**Formal statement B**

```lean
theorem X {F V : Type*} [AddCommGroup V] [Field F]
  [Module F V] [FiniteDimensional F V] {S T : End F V}
  (h1 : card (T.Eigenvalues) = finrank F V)
  (h2 : ∀ v : V, ∃ c : F, v ∈ eigenspace S c ↔ ∃ c : F, v ∈ eigenspace T c) :
  S * T = T * S
```

## t129

**Informal statement**

In this problem, $a$ and $b$ are integers, such that $a \ge b.$

If $a+b\equiv 2\pmod{10}$ and $2a+b\equiv 1\pmod{10}$, then what is the last digit of $a-b$? Show that it is 6.

**Formal statement A**

```lean
theorem X (a b : ℕ) (h₀ : b ≤ a) (h₁ : (a + b) ≡ 2 [MOD 10])
  (h₂ : (2 * a + b) ≡ 1 [MOD 10]) : (a - b) % 10 = 6
```

**Formal statement B**

```lean
theorem X (a b : ℕ) (h₀ : 0 < a ∧ 0 < b ∧ b ≤ a) (h₁ : (a + b) % 10 = 2)
  (h₂ : (2 * a + b) % 10 = 1) : (a - b) % 10 = 6
```

## t158

**Informal statement**

Find the smallest positive integer $k$ such that, for every positive integer $n$, $6n+k$ is relatively prime to each of $6n+3$, $6n+2$, and $6n+1$. Show that it is 5.

**Formal statement A**

```lean
theorem X
  (S : Set ℕ)
  (hS: S = {k | ∀ n:ℕ, 0 < n → Nat.gcd (6 * n + k) (6 * n + 3) = 1 ∧Nat.gcd (6 * n + k) (6 * n + 2) = 1 ∧ Nat.gcd (6 * n + k) (6 * n + 1) = 1}) :
  IsLeast S 5
```

**Formal statement B**

```lean
theorem X (k : ℕ) (h₀ : 0 < k) (h₁ : ∀ n, Nat.gcd (6 * n + k) (6 * n + 3) = 1)
    (h₂ : ∀ n, Nat.gcd (6 * n + k) (6 * n + 2) = 1) (h₃ : ∀ n, Nat.gcd (6 * n + k) (6 * n + 1) = 1) :
    5 ≤ k
```

## t077

**Informal statement**

A rectangular patio has an area of $180$ square feet and a perimeter of $54$ feet. What is the length of the diagonal (in feet) squared? Show that it is 369.

**Formal statement A**

```lean
theorem X (a b : ℝ) (h₁ : a * b = 180) (h₂ : 2 * (a + b) = 54) :
    a ^ 2 + b ^ 2 = 369
```

**Formal statement B**

```lean
theorem X
  (T : Affine.Triangle ℝ (EuclideanSpace ℝ (Fin 2)))
  (A B C : EuclideanSpace ℝ (Fin 2))
  (hA : A = T.points 0)
  (hB : B = T.points 1)
  (hC : C = T.points 2)
  (a b : ℝ)
  (h₀ : dist A B = a ∧ dist B C = b)
  (h₁ : a * b = 180)
  (h₂ : 2 * (a + b) = 54)
  (θ : ℝ)
  (hθ₀ : θ = EuclideanGeometry.angle A B C)
  (hθ₀ : θ = Real.pi / 2) :
  (dist A C) ^ 2 = 369
```

## t031

**Informal statement**

In the complex plane, let $A$ be the set of solutions to $z^{3}-8=0$ and let $B$ be the set of solutions to $z^{3}-8z^{2}-8z+64=0.$ What is the greatest distance between a point of $A$ and a point of $B?$

$\textbf{(A) } 2\sqrt{3} \qquad \textbf{(B) } 6 \qquad \textbf{(C) } 9 \qquad \textbf{(D) } 2\sqrt{21} \qquad \textbf{(E) } 9+\sqrt{3}$ Show that it is \textbf{(D) } 2\sqrt{21}.

**Formal statement A**

```lean
theorem X
  (A B : Set ℂ)
  (D : Set ℝ)
  (hA : A = {x:ℂ | x ^ 3 - 8 = 0})
  (hB : B = {x:ℂ | x ^ 3 - 8 * x ^ 2 - 8 * x + 64 = 0})
  (hD : D = {d:ℝ | ∃ a b:ℂ, a ∈ A ∧ b ∈ B ∧ d = Complex.normSq (a - b)}):
  IsGreatest D ((2:ℝ) * Real.sqrt 21)
```

**Formal statement B**

```lean
theorem X (a b : ℂ) (h₀ : a ^ 3 - 8 = 0) (h₁ : b ^ 3 - 8 * b ^ 2 - 8 * b + 64 = 0) :
    Complex.abs (a - b) ≤ 2 * Real.sqrt 21
```

## t011

**Informal statement**

Show that for any real-valued function $a$ on the natural numbers such that $\forall i \in \mathbb{N}, a_i \geq 0$, if $prod_{i=0}^{n-1} a_i = 1$, then $sum_{i=0}^{n-1} a_i \geq n$.

**Formal statement A**

```lean
theorem X (a : ℕ → ℝ) (n : ℕ)
  (h₀: ∀ x:ℕ, 0 ≤ a x)
  (h₀ : Finset.prod (Finset.range n) a = 1) : Finset.sum (Finset.range n) a ≥ n
```

**Formal statement B**

```lean
theorem X (a : ℕ → NNReal) (n : ℕ)
  (h₀ : Finset.prod (Finset.range n) a = 1) : Finset.sum (Finset.range n) a ≥ n
```

## t012

**Informal statement**

Let $r$ be a real number such that $r^{\frac{1}{3}} + \frac{1}{r^{\frac{1}{3}}} = 3$. Show that $r^3 + \frac{1}{r^3} = 5778$.

**Formal statement A**

```lean
theorem X
  (r : ℝ)
  (h₀ : r^((1 : ℝ)/3) + 1/r^((1 : ℝ)/3) = 3)
  (h₁: r ^ (1 / 3 : ℝ) ≠ (1 / 2 : ℝ) * (-r) ^ (1 / 3 : ℝ)) :
  r^3 + 1/(r^3) = 5778
```

**Formal statement B**

```lean
theorem X (r : ℝ)
    (h₀ : r ^ ((1 : ℝ) / 3) + 1 / r ^ ((1 : ℝ) / 3) = 3) : r ^ 3 + 1 / r ^ 3 = 5778
```

## t244

**Informal statement**

Let $\mathbf{x}_1, \mathbf{x}_2, \ldots$ be a sequence of the points of the product space $\prod X_\alpha$.  Show that this sequence converges to the point $\mathbf{x}$ if and only if the sequence $\pi_\alpha(\mathbf{x}_i)$ converges to $\pi_\alpha(\mathbf{x})$ for each $\alpha$.

**Formal statement A**

```lean
theorem X
  {ι : Type*}
  {f : ι → Type*} {x : ℕ → Πa, f a}
  (y : Πi, f i)
  [Πa, TopologicalSpace (f a)] :
  Tendsto x atTop (𝓝 y) ↔ ∀ i, Tendsto (λ j => (x j) i) atTop (𝓝 (y i))
```

**Formal statement B**

```lean
theorem X
  {n : ℕ}
  {f : Fin n → Type*} {x : ℕ → Πa, f a}
  (y : Πi, f i)
  [Πa, TopologicalSpace (f a)] :
  Tendsto x atTop (𝓝 y) ↔ ∀ i, Tendsto (λ j => (x j) i) atTop (𝓝 (y i))
```

## t205

**Informal statement**

Use Lagrange's Theorem in the multiplicative group $(\mathbb{Z} / p \mathbb{Z})^{\times}$to prove Fermat's Little Theorem: if $p$ is a prime then $a^{p} \equiv a(\bmod p)$ for all $a \in \mathbb{Z}$.

**Formal statement A**

```lean
theorem X (p : ℕ) (hp : Nat.Prime p) (a : ℤ) :
  a ^ p ≡ a [ZMOD p]
```

**Formal statement B**

```lean
theorem X (p : ℕ) (hp : Nat.Prime p) (a : ℕ) :
  Nat.Coprime a p → a ^ p ≡ a [ZMOD p]
```

## t021

**Informal statement**

For how many positive integers $m$ does there exist at least one positive integer n such that $m \cdot n \le m + n$?

$ \textbf{(A) } 4\qquad \textbf{(B) } 6\qquad \textbf{(C) } 9\qquad \textbf{(D) } 12\qquad \textbf{(E) } \text{infinitely many} $ Show that it is \textbf{(E) } \text{infinitely many}.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) : ∃ m, m > n ∧ ∃ p, m * p ≤ m + p
```

**Formal statement B**

```lean
theorem X
  (S: Set ℕ)
  (hS : S = {m | 0 < m ∧ (∃ n, 0 < n ∧ m * n ≤ m + n)}) :
  Set.Infinite S
```

## t142

**Informal statement**

What is the tens digit in the sum $11^1 + 11^2 + 11^3 + \ldots + 11^9$? Show that it is 5.

**Formal statement A**

```lean
theorem X : (∑ k in Finset.Icc 1 9, 11 ^ k) % 100 = 59
```

**Formal statement B**

```lean
theorem X
  (x : ℕ)
  (h₀ : x = ∑ k ∈ Finset.Icc 1 9, 11 ^ k)
  (L : List ℕ)
  (h₁ : L = (Nat.digits 10 x).drop 1)
  (h₂ : L ≠ []) :
  List.head L h₂ = 5
```

## t240

**Informal statement**

If $p=2^{n}+1$ is a Fermat prime, show that 3 is a primitive root modulo $p$.

**Formal statement A**

```lean
theorem X {p n : ℕ} (hp : p.Prime) (hpn : p = 2^n + 1) :
  IsPrimitiveRoot (3 : ZMod p) p
```

**Formal statement B**

```lean
theorem X {p n : ℕ} (hp : p.Prime) (hpn : p = 2^n + 1) :
  IsPrimitiveRoot 3 p
```

## t184

**Informal statement**

Let $V$ be a vector space over an infinite field $F$. Prove that $V$ is not the union of finitely many proper subspaces.

**Formal statement A**

```lean
theorem X {K V : Type*} [Field K] [AddCommGroup V]
  [Module K V] {ι : Type*} [Fintype ι] (γ : ι → Submodule K V)
  (h : ∀ i : ι, γ i ≠ ⊤) :
  (⋂ (i : ι), (γ i : Set V)) ≠ ⊤
```

**Formal statement B**

```lean
theorem X {K V : Type*} [Field K] [Infinite K] [AddCommGroup V]
  [Module K V] {ι : Type*} [Fintype ι] (γ : ι → Submodule K V)
  (h : ∀ i : ι, γ i ≠ ⊤) :
  (⋃ (i : ι), (γ i : Set V)) ≠ ⊤
```

## t005

**Informal statement**

Find $(\log_2 x)^2$ if $\log_2 (\log_8 x) = \log_8 (\log_2 x)$. Show that it is 027.

**Formal statement A**

```lean
theorem X (x : ℝ) (h₀ : 0 < x)
  (h₁ : Real.logb 2 (Real.logb 8 x) = Real.logb 8 (Real.logb 2 x)) : Real.logb 2 x ^ 2 = 27
```

**Formal statement B**

```lean
theorem X (x : ℝ)  (h₀ : 1 < x)
  (h₁ : Real.logb 2 (Real.logb 8 x) = Real.logb 8 (Real.logb 2 x)) : Real.logb 2 x ^ 2 = 27
```

## t246

**Informal statement**

Let $\left\{A_{\alpha}\right\}$ be a collection of connected subspaces of $X$; let $A$ be a connected subset of $X$. Show that if $A \cap A_{\alpha} \neq \varnothing$ for all $\alpha$, then $A \cup\left(\bigcup A_{\alpha}\right)$ is connected.

**Formal statement A**

```lean
theorem X {X α : Type*} [TopologicalSpace X]
  {A : α → Set X}
  (hAa : ∀ a, IsConnected (A a))
  (A₀ : Set X)
  (hA : IsConnected A₀)
  (h : ∀ a, A₀ ∩ A a ≠ ∅) :
  IsConnected (A₀ ∪ (⋃ a, A a))
```

**Formal statement B**

```lean
theorem X {X : Type*} [TopologicalSpace X]
  [TopologicalSpace X] {A : ℕ → Set X}
  (hAn : ∀ n, IsConnected (A n))
  (A₀ : Set X)
  (hA : IsConnected A₀)
  (h : ∀ n, A₀ ∩ A n ≠ ∅) :
  IsConnected (A₀ ∪ (⋃ n, A n))
```

## t215

**Informal statement**

Prove that if $|G|=105$ then $G$ has a normal Sylow 5 -subgroup and a normal Sylow 7-subgroup.

**Formal statement A**

```lean
theorem X {G : Type*} [Fintype G] [Group G]
  (hG : card G = 105) :
  Nonempty (Sylow 5 G) ∧ Nonempty (Sylow 7 G)
```

**Formal statement B**

```lean
theorem X {G : Type*} [Fintype G] [Group G]
  (hG : card G = 105) :
  (∃ (P : Sylow 5 G), P.Normal) ∧ (∃ (P : Sylow 7 G), P.Normal)
```

## t216

**Informal statement**

Prove that if $P \in \operatorname{Syl}_{p}(G)$ and $H$ is a subgroup of $G$ containing $P$ then $P \in \operatorname{Syl}_{p}(H)$.

**Formal statement A**

```lean
theorem X {p : ℕ} {G : Type*} [Group G]
  {P : Subgroup G} (hP : IsPGroup p P) (H : Subgroup G)
  (hH : P ≤ H) : IsPGroup p H
```

**Formal statement B**

```lean
theorem X {p : ℕ} {G : Type*} [Group G]
  {P : Sylow p G} (H : Subgroup G) (hH : P ≤ H) :
  IsPGroup p (P.subgroupOf H) ∧
  ∀ (Q : Subgroup H), IsPGroup p Q → (P.subgroupOf H) ≤ Q → Q = (P.subgroupOf H)
```

## t224

**Informal statement**

If $G$ is a finite group, prove that, given $a \in G$, there is a positive integer $n$, depending on $a$, such that $a^n = e$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G]
  [Fintype G] (a : G) : ∃ (n : ℕ), n > 0 ∧ a ^ n = 1
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G]
  [Fintype G] (a : G) : ∃ (n : ℕ), a ^ n = 1
```

## t279

**Informal statement**

Suppose $f$ is a real, three times differentiable function on $[-1,1]$, such that $f(-1)=0, \quad f(0)=0, \quad f(1)=1, \quad f^{\prime}(0)=0 .$ Prove that $f^{(3)}(x) \geq 3$ for some $x \in(-1,1)$.

**Formal statement A**

```lean
theorem X
  {f : ℝ → ℝ}
  (hf' : DifferentiableOn ℝ f (Set.Icc (-1) 1))
  (hf'' : DifferentiableOn ℝ (deriv f) (Set.Icc (-1) 1))
  (hf''' : DifferentiableOn ℝ (deriv (deriv f)) (Set.Icc (-1) 1))
  (hf0 : f (-1) = 0)
  (hf1 : f 0 = 0)
  (hf2 : f 1 = 1)
  (hf3 : deriv f 0 = 0) :
  ∃ x, x ∈ Set.Ioo (-1 : ℝ) 1 ∧ deriv (deriv (deriv f)) x ≥ 3
```

**Formal statement B**

```lean
theorem X
  {f : ℝ → ℝ}
  (hf' : DifferentiableOn ℝ f (Set.Icc (-1) 1))
  (hf'' : DifferentiableOn ℝ (deriv f) (Set.Icc 1 1))
  (hf''' : DifferentiableOn ℝ (deriv (deriv f)) (Set.Icc 1 1))
  (hf0 : f (-1) = 0)
  (hf1 : f 0 = 0)
  (hf2 : f 1 = 1)
  (hf3 : deriv f 0 = 0) :
  ∃ x, x ∈ Set.Ioo (-1 : ℝ) 1 ∧ deriv (deriv (deriv f)) x ≥ 3
```

## t033

**Informal statement**

The number $a=\frac{p}{q}$, where $p$ and $q$ are relatively prime positive integers, has the property that the sum of all real numbers $x$ satisfying
$ \lfloor x \rfloor \cdot \{x\} = a \cdot x^2$
is $420$, where $\lfloor x \rfloor$ denotes the greatest integer less than or equal to $x$ and $\{x\}=x- \lfloor x \rfloor$ denotes the fractional part of $x$. What is $p+q$?

$\textbf{(A) } 245 \qquad \textbf{(B) } 593 \qquad \textbf{(C) } 929 \qquad \textbf{(D) } 1331 \qquad \textbf{(E) } 1332$ Show that it is \textbf{(C) } 929.

**Formal statement A**

```lean
theorem X (a : ℚ) (S : Finset ℝ)
    (h₀ : ∀ x : ℝ, x ∈ S ↔ ↑⌊x⌋ * (x - ↑⌊x⌋) = ↑a * x ^ 2) (h₁ : (∑ k in S, k) = 420) :
    ↑a.den + a.num = 929
```

**Formal statement B**

```lean
theorem X
  (a : ℚ)
  (ha₀ : 0 < a)
  (S : Finset ℝ)
  (h₀ : ∀ (x : ℝ), x ∈ S ↔ ↑⌊x⌋ * (x - ↑⌊x⌋) = ↑a * x ^ 2)
  (h₁ : (∑ k ∈ S, k) = 420) :
  ↑a.den + a.num = 929
```

## t159

**Informal statement**

What is the least positive integer $n$ such that $80325$ divides $n!$? Show that it is 17.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) (h₁ : 80325 ∣ n !) : 17 ≤ n
```

**Formal statement B**

```lean
theorem X
  (S : Set ℕ)
  (hS: S = {n | 0 < n ∧  80325 ∣ Nat.factorial n}) :
  IsLeast S 17
```

## t009

**Informal statement**

The function $f_{}^{}$ has the property that, for each real number $x,\,$
<center>$f(x)+f(x-1) = x^2.\,$</center>
If $f(19)=94,\,$ what is the remainder when $f(94)\,$ is divided by $1000$? Show that it is 561.

**Formal statement A**

```lean
theorem X (x : ℤ) (f : ℤ → ℤ) (h0 : f x + f (x - 1) = x ^ 2) (h1 : f 19 = 94) :
    f 94 % 1000 = 561
```

**Formal statement B**

```lean
theorem X (f : ℤ → ℤ) (h₁ : ∀ x, f x + f (x-1) = x^2) (h₂ : f 19 = 94) : f 94 % 1000 = 561
```

## t237

**Informal statement**

If $n$ is not a prime, show that $(n-1) ! \equiv 0(n)$, except when $n=4$.

**Formal statement A**

```lean
theorem X {n : ℕ+} (hn0 : ¬ n.Prime) :
  Nat.factorial (n-1) ≡ 0 [MOD n] ↔ n ≠ 4
```

**Formal statement B**

```lean
theorem X {n : ℕ} (hn0 : ¬ n.Prime) (hn1 : n ≠ 4) :
  Nat.factorial (n-1) ≡ 0 [MOD n]
```

## t231

**Informal statement**

If $p$ is a prime, show that $q(x) = 1 + x + x^2 + \cdots x^{p - 1}$ is irreducible in $Q[x]$.

**Formal statement A**

```lean
theorem X {p : ℕ} (hp : Nat.Prime p) :
  Irreducible (∑ i : Finset.range p, X ^ p : Polynomial ℚ)
```

**Formal statement B**

```lean
theorem X {p : ℕ} (hp : Nat.Prime p) :
  Irreducible (∑ i in Finset.range p, X ^ i : Polynomial ℚ)
```

## t150

**Informal statement**

What integer $n$ satisfies $0\le n<{101}$ and $$123456\equiv n\pmod {101}~?$$ Show that it is 34.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : n < 101)
 (h₁ : 123456 ≡ n [MOD 101]) :
 n = 34
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : n < 101) (h₁ : 101 ∣ 123456 - n) : n = 34
```

## t277

**Informal statement**

Let $E$ be a bounded set in $R^{1}$. Prove that there exists a real function $f$ such that $f$ is uniformly continuous and is not bounded on $E$.

**Formal statement A**

```lean
theorem X
  (E : Set ℝ) (h : Bornology.IsBounded E) :
  ∃ f : ℝ → ℝ, UniformContinuousOn f E ∧ ¬ Bornology.IsBounded (Set.image f E)
```

**Formal statement B**

```lean
theorem X
  (E : Set ℝ) :
  ∃ f : ℝ → ℝ, UniformContinuousOn f E ∧ ¬ Bornology.IsBounded (Set.image f E)
```

## t178

**Informal statement**

Let $I, J$ be ideals in a ring $R$. Prove that the residue of any element of $I \cap J$ in $R / I J$ is nilpotent.

**Formal statement A**

```lean
theorem X {R : Type*} [CommRing R]
  [NoZeroDivisors R] (I J : Ideal R) (x : ↑(I ⊓ J)) :
  IsNilpotent ((Ideal.Quotient.mk (I*J)) x)
```

**Formal statement B**

```lean
theorem X {R : Type*} [CommRing R]
  (I J : Ideal R) (x : ↑(I ⊓ J)) :
  IsNilpotent ((Ideal.Quotient.mk (I*J)) x)
```

## t146

**Informal statement**

What digit must be placed in the blank to make the four-digit integer $20\_7$ a multiple of 11? Show that it is 5.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : n ≤ 9) (h₁ : 11 ∣ 20 * 100 + 10 * n + 7) : n = 5
```

**Formal statement B**

```lean
theorem X
  (n x : ℕ)
  (h₀ : Nat.digits 10 x = [7, n, 0, 2])
  (h₁ : 11 ∣ x) :
  n = 5
```

## t083

**Informal statement**

We have two geometric sequences of positive real numbers: $$6,a,b\text{ and }\frac{1}{b},a,54$$Solve for $a$. Show that it is 3\sqrt{2}.

**Formal statement A**

```lean
theorem X (a b : NNReal) (h₀ : 0 < a ∧ 0 < b) (h₁ : a ^ 2 = 6 * b)
    (h₂ : a ^ 2 = 54 / b) : a = 3 * NNReal.sqrt 2
```

**Formal statement B**

```lean
theorem X
  (a b : NNReal)
  (h₀ : 0 < a ∧ 0 < b)
  (S₁ S₂ : Fin 3 → NNReal)
  (h₁ : S₁ 0 = 6 ∧ S₁ 1 = a ∧ S₁ 2 = b)
  (h₂ : S₂ 0 = 1 / b ∧ S₁ 1 = a ∧ S₁ 2 = 54)
  (h₃ : ∃! r, r ≠ 0 ∧ r ≠ 1 ∧ ∀ n, n < 2 → S₁ n * r = S₁ (n + 1))
  (h₄ : ∃! r, r ≠ 0 ∧ r ≠ 1 ∧ ∀ n, S₂ n * r = S₂ (n + 1)) :
  a = 3 * NNReal.sqrt 2
```

## t041

**Informal statement**

Suppose that $a$ and $b$ are nonzero real numbers, and that the [[equation]] $x^2 + ax + b = 0$ has solutions $a$ and $b$. Then the pair $(a,b)$ is

$\mathrm{(A)}\ (-2,1)
\qquad\mathrm{(B)}\ (-1,2)
\qquad\mathrm{(C)}\ (1,-2)
\qquad\mathrm{(D)}\ (2,-1)
\qquad\mathrm{(E)}\ (4,4)$ Show that it is \mathrm{(C)}\ (1,-2).

**Formal statement A**

```lean
theorem X (a b : ℝ) (h₀ : a ≠ 0 ∧ b ≠ 0)
  (h₁ : ∀ x, x ^ 2 + a * x + b = (x - a) * (x - b)) : a = 1 ∧ b = -2
```

**Formal statement B**

```lean
theorem X 
  (a b : ℝ)
  (f : ℝ → ℝ)
  (h₀ : a ≠ 0 ∧ b ≠ 0)
  (h₁: f = fun x => x ^ 2 + a * x + b)
  (h₂: f a = 0)
  (h₃ : f b = 0) : 
  a = 1 ∧ b = -2
```

## t115

**Informal statement**

If $f(x)=5x-12$, find a value for $x$ so that $f^{-1}(x)=f(x+1)$. Show that it is \frac{47}{24}.

**Formal statement A**

```lean
theorem X
  (f : ℝ → ℝ)
  (hf : f = fun x ↦ 5 * x - 12)
  (x : ℝ)
  (hx : f ⁻¹' {x} = {f (x + 1)}) :
  x = 47 / 24
```

**Formal statement B**

```lean
theorem X (x : ℝ) (σ : Equiv ℝ ℝ) (h₀ : ∀ x, σ.1 x = 5 * x - 12)
  (h₁ : σ.1 (x + 1) = σ.2 x) : x = 47 / 24
```

## t139

**Informal statement**

One morning each member of Angela's family drank an 8-ounce mixture of coffee with milk. The amounts of coffee and milk varied from cup to cup, but were never zero. Angela drank a quarter of the total amount of milk and a sixth of the total amount of coffee. How many people are in the family? Show that it is 5.

**Formal statement A**

```lean
theorem X
  (milk coffee n : ℕ+)
  (h₀ : (milk:ℝ)/4 + (coffee:ℝ)/6 = 8)
  (h₁: milk + coffee = n * 8) :
  n = 5
```

**Formal statement B**

```lean
theorem X (x y n : ℕ+) (h₀ : ↑x / (4 : ℝ) + y / 6 = (x + y) / n) : n = 5
```

## t111

**Informal statement**

On planet Larky, 7 ligs = 4 lags, and 9 lags = 20 lugs. How many ligs are equivalent to 80 lugs? Show that it is 63.

**Formal statement A**

```lean
theorem X (a b c : ℝ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c) (h₁ : 9 * b = 20 * c)
    (h₂ : 7 * a = 4 * b) : 63 * a = 80 * c
```

**Formal statement B**

```lean
theorem X (a b c x : ℝ) (h₁ : 9 * b = 20 * c)
  (h₂ : 7 * a = 4 * b) (h₃ : x * a = 80 * c) : x = 63
```

## t053

**Informal statement**

Let $a,b$ be two natural numbers. When we divide $a^2+b^2$ by $a+b$, we the the remainder $r$ and the quotient $q.$ Determine all pairs $(a, b)$ for which $q^2 + r = 1977.$ Show that it is (a,b)=(37,50) , (7, 50).

**Formal statement A**

```lean
theorem X
  (a b q r : ℕ)
  (hp: 0 < a ∧ 0 < b)
  (h₀ : r = (a ^ 2 + b ^ 2) % (a + b))
  (h₁ : q = (a ^ 2 + b ^ 2) / (a + b))
  (h₂ : q ^ 2 + r = 1977) :
  (a = 7 ∧ b = 50) ∨ (a = 37 ∧ b = 50) ∨ (a = 50 ∧ b = 7) ∨ (a = 50 ∧ b = 37)
```

**Formal statement B**

```lean
theorem X (a b q r : ℕ) (h₀ : r < a + b) (h₁ : a ^ 2 + b ^ 2 = (a + b) * q + r)
  (h₂ : q ^ 2 + r = 1977) :
  abs ((a : ℤ) - 22) = 15 ∧ abs ((b : ℤ) - 22) = 28 ∨
    abs ((a : ℤ) - 22) = 28 ∧ abs ((b : ℤ) - 22) = 15
```

## t187

**Informal statement**

Suppose that $V$ is finite dimensional and that $T \in \mathcal{L}(V, W)$. Prove that there exists a subspace $U$ of $V$ such that $U \cap \operatorname{null} T=\{0\}$ and range $T=\{T u: u \in U\}$.

**Formal statement A**

```lean
theorem X {F V W : Type*} [AddCommGroup V]
  [AddCommGroup W] [Field F] [Module F V] [FiniteDimensional F V] [Module F W]
  (L : V →ₗ[F] W) :
  ∃ U : Submodule F V, U ⊓ (ker L) = ⊥ ∧
  (range L = range (domRestrict L U))
```

**Formal statement B**

```lean
theorem X {F V W : Type*}  [AddCommGroup V]
  [AddCommGroup W] [Field F] [Module F V] [Module F W]
  (L : V →ₗ[F] W) :
  ∃ U : Submodule F V, U ⊓ (ker L) = ⊥ ∧
  (range L = range (domRestrict L U))
```

## t245

**Informal statement**

Let $p: X \rightarrow Y$ be a continuous map. Show that if there is a continuous map $f: Y \rightarrow X$ such that $p \circ f$ equals the identity map of $Y$, then $p$ is a quotient map.

**Formal statement A**

```lean
theorem X {X Y : Type*} [TopologicalSpace X]
  [TopologicalSpace Y] (p : X → Y) (h : Continuous p) :
  QuotientMap p ↔ ∃ (f : Y → X), Continuous f ∧ p ∘ f = id
```

**Formal statement B**

```lean
theorem X {X Y : Type*} [TopologicalSpace X]
  [TopologicalSpace Y] (p : X → Y) (h : Continuous p) :
  (∃ (f : Y → X), Continuous f ∧ p ∘ f = id) → QuotientMap p
```

## t051

**Informal statement**

Prove that for every natural number $n$, and for every real number $x \neq \frac{k\pi}{2^t}$ ($t=0,1, \dots, n$; $k$ any integer)
$ \frac{1}{\sin{2x}}+\frac{1}{\sin{4x}}+\dots+\frac{1}{\sin{2^nx}}=\cot{x}-\cot{2^nx}  $

**Formal statement A**

```lean
theorem X
  (n : ℕ)
  (x : ℝ)
  (h₀ : ∀ k : ℕ, k ≤ n → ∀ m : ℤ, x ≠ m * π / (2^k))
  (h₁ : 0 < n) :
  ∑ k ∈ Finset.Icc 1 n, (1 / Real.sin ((2^k) * x)) = 1 / Real.tan x - 1 / Real.tan ((2^n) * x)
```

**Formal statement B**

```lean
theorem X (n : ℕ) (x : ℝ) (h₀ : ∀ k : ℕ, 0 < k → ∀ m : ℤ, x ≠ m * Real.pi / 2 ^ k)
  (h₁ : 0 < n) :
  (∑ k in Finset.Icc 1 n, 1 / Real.sin (2 ^ k * x)) = 1 / Real.tan x - 1 / Real.tan (2 ^ n * x)
```

## t024

**Informal statement**

What is the minimum value of $f(x)=\left|x-1\right| + \left|2x-1\right| + \left|3x-1\right| + \cdots + \left|119x - 1 \right|$?

$\textbf{(A)}\ 49 \qquad \textbf{(B)}\ 50 \qquad \textbf{(C)}\ 51 \qquad \textbf{(D)}\ 52 \qquad \textbf{(E)}\ 53$ Show that it is 49\ \textbf{(A)}.

**Formal statement A**

```lean
theorem X (x : ℝ) : 49 ≤ ∑ k:ℤ in Finset.Icc 1 119, abs (↑k * x - 1)
```

**Formal statement B**

```lean
theorem X : IsLeast {x | ∃ t : ℝ, x = ∑ i in Finset.range 119, |(i+1)*t - 1|} 49
```

## t285

**Informal statement**

Prove that the power series $\sum zn/n$ converges at every point of the unit circle except $z = 1$.

**Formal statement A**

```lean
theorem X (z : ℂ) (hz : abs z = 1) (s : ℕ → ℂ)
    (h : s = (λ n => ∑ i in (range n), z ^ (i + 1) / (i + 1))) :
    (∃ z₀, Tendsto s atTop (𝓝 z₀)) ↔ z ≠ 1
```

**Formal statement B**

```lean
theorem X (z : ℂ) (hz : abs z = 1) (hz2 : z ≠ 1) (s : ℕ → ℂ)
    (h : s = (λ n => ∑ i in (range n), i * z / i)) :
    ∃ z, Tendsto s atTop (𝓝 z)
```

## t218

**Informal statement**

Let $\varphi: R \rightarrow S$ be a surjective homomorphism of rings. Prove that the image of the center of $R$ is contained in the center of $S$.

**Formal statement A**

```lean
theorem X {R S : Type*} [Ring R] [Ring S]
  {φ : R →+* S} (hf : Function.Surjective φ) :
  φ '' (center R) ⊂ center S
```

**Formal statement B**

```lean
theorem X {R S : Type*} [Ring R] [Ring S]
  {φ : R →+* S} (hf : Function.Surjective φ) :
  φ '' (center R) ⊆ center S
```
