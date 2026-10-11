# Tagging batch 06 (40 items)

## t128

**Informal statement**

Find $n$ if $\gcd(n,40) = 10$ and $\mathop{\text{lcm}}[n,40] = 280$. Show that it is 70.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) (h₁ : Nat.gcd n 40 = 10)
    (h₂ : Nat.lcm n 40 = 280) : n = 70
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₁ : Nat.gcd n 40 = 10)
  (h₂ : Nat.lcm n 40 = 280) : n = 70
```

## t212

**Informal statement**

Prove that a group of order 312 has a normal Sylow $p$-subgroup for some prime $p$ dividing its order.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (hG : card G = 312) :
  ∃ (p : ℕ) (P : Sylow p G), p.Prime ∧ (p ∣ card G) ∧ P.Normal
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (hG : card G = 312) :
  ∃ (p : ℕ) (P : Sylow p G), P.Normal
```

## t075

**Informal statement**

Solve for $a$: $\dfrac{8^{-1}}{4^{-1}}-a^{-1}=1$. Show that it is -2.

**Formal statement A**

```lean
theorem X (a : ℝ) (h₀ : a ≠ 0) (h₁ : 8⁻¹ / 4⁻¹ - a⁻¹ = 1) : a = -2
```

**Formal statement B**

```lean
theorem X (a : ℝ) (h₀ : (8 : ℝ)⁻¹ / (4 : ℝ)⁻¹ - a⁻¹ = (1 : ℝ)) : a = -2
```

## t019

**Informal statement**

Both roots of the quadratic equation $x^2 - 63x + k = 0$ are prime numbers. The number of possible values of $k$ is 

$\text{(A)}\ 0 \qquad \text{(B)}\ 1 \qquad \text{(C)}\ 2 \qquad \text{(D)}\ 4 \qquad \text{(E) more than 4}$ Show that it is \text{(B)}\ 1.

**Formal statement A**

```lean
theorem X :
  ∃! k, ∃ a b:ℕ, (Nat.Prime a ∧ Nat.Prime b ∧ a ≠ b ∧ (∀ f : ℝ → ℝ, (f = fun x:ℝ ↦ x ^ 2 - 63 * x + k ) → f (a:ℝ) = 0 ∧ f (b:ℝ) = 0))
```

**Formal statement B**

```lean
theorem X (f : ℝ → ℝ) (k : ℝ) (a b : ℕ) (h₀ : ∀ x, f x = x ^ 2 - 63 * x + k)
  (h₁ : f a = 0 ∧ f b = 0) (h₂ : a ≠ b) (h₃ : Nat.Prime a ∧ Nat.Prime b) : k = 122
```

## t267

**Informal statement**

Suppose $E\subset\mathbb{R}^k$ is uncountable, and let $P$ be the set of condensation points of $E$. Prove that $P$ is perfect.

**Formal statement A**

```lean
theorem X (k : ℕ) (E P : Set (EuclideanSpace ℝ (Fin k)))
  (hE : E.Nonempty ∧ ¬ Set.Countable E)
  (hP : P = {x | ∀ U ∈ 𝓝 x, ¬ Set.Countable (P ∩ E)}) :
  IsClosed P ∧ P = {x | ClusterPt x (𝓟 P)}
```

**Formal statement B**

```lean
theorem X (k : ℕ) (E P : Set (EuclideanSpace ℝ (Fin k)))
  (hE : ¬ Set.Countable E)
  (hP : P = {x | ∀ U ∈ 𝓝 x, ¬ Set.Countable (U ∩ E)}) :
  Perfect P
```

## t181

**Informal statement**

Prove that $x^2+x+1$ is irreducible in the field $\mathbb{F}_2$.

**Formal statement A**

```lean
theorem X {F : Type*} [Field F] [Fintype F] (hF : card F = 2) :
  Irreducible (X ^ 2 + X + 1 : Polynomial F)
```

**Formal statement B**

```lean
theorem X {F : Type*} [Field F] [Fintype F] (hF : card F = 7) :
  Irreducible (X ^ 2 + 1 : Polynomial F)
```

## t276

**Informal statement**

Suppose $K$ and $F$ are disjoint sets in a metric space $X, K$ is compact, $F$ is closed. Prove that there exists $\delta>0$ such that $d(p, q)>\delta$ if $p \in K, q \in F$.

**Formal statement A**

```lean
theorem X {X : Type*} [MetricSpace X]
  (K F : Set X) (hK : IsCompact K) (hF : IsClosed F) (hKF : Disjoint K F) :
  ∃ (δ : ℝ), δ > 0 ∧ ∀ (p q : X), p ∈ K → q ∈ F → dist p q > δ
```

**Formal statement B**

```lean
theorem X {X : Type*} [MetricSpace X]
  (K F : Set X) (hK : IsCompact K) (hF : IsClosed F) (hKF : Disjoint K F) :
  ∃ (δ : ℝ), δ > 0 ∧ ∀ (p q : X), p ∈ K → q ∈ F → dist p q ≥ δ
```

## t105

**Informal statement**

In a rectangular coordinate system, the line $3y = x$ intersects the line $2x + 5y = 11$ at point $A$. What is the sum of the coordinates of point $A$? Show that it is 4.

**Formal statement A**

```lean
theorem X (x y : ℝ) (h₀ : 3 * y = x) (h₁ : 2 * x + 5 * y = 11) : x + y = 4
```

**Formal statement B**

```lean
theorem X
  (L₁ L₂ I : Set (EuclideanSpace ℝ (Fin 2)))
  (hL₁ : L₁ = { x | x 0 = 3 * (x 1)})
  (hL₂ : L₂ = { x | 2 * (x 0) + 5 * (x 1) = 11})
  (hI : I = L₁ ∩ L₂)
  (A : EuclideanSpace ℝ (Fin 2))
  (hA : A ∈ I) :
  A 0 + A 1 = 4
```

## t039

**Informal statement**

What is the least possible value of $(xy-1)^2+(x+y)^2$ for real numbers $x$ and $y$?

$\textbf{(A)} ~0\qquad\textbf{(B)} ~\frac{1}{4}\qquad\textbf{(C)} ~\frac{1}{2} \qquad\textbf{(D)} ~1 \qquad\textbf{(E)} Show that it is \textbf{(D)} ~1.

**Formal statement A**

```lean
theorem X (x y : ℝ) : 1 ≤ (x * y - 1) ^ 2 + (x + y) ^ 2
```

**Formal statement B**

```lean
theorem X
  (S : Set ℝ)
  (hS : S = {z | ∃ x y:ℝ, z = (x * y - 1) ^ 2 + (x + y) ^ 2}) :
  IsLeast S 1
```

## t135

**Informal statement**

Tim is doing a cakewalk with $11$ steps. He takes his first step on step $1$ and takes a total of $139$ steps, walking in a circle (so that after the 11th step he reaches the first step again). Which step of the cakewalk does he end on? Show that it is 7.

**Formal statement A**

```lean
theorem X
  (x p : ℕ)
  (f : ℕ → ℝ)
  (h₀ : Function.Periodic f p)
  (h₁ : f 11 = f 0)
  (h₂: f 139 = f x) :
  x = 7
```

**Formal statement B**

```lean
theorem X : 139 % 11 = 7
```

## t145

**Informal statement**

What positive two-digit integer is exactly twice the sum of its digits? Show that it is 18.

**Formal statement A**

```lean
theorem X
  (x : ℕ)
  (h₀ : 0 < x)
  (h₁ : (Nat.digits 10 x).length = 2)
  (h₁ : 2 * (Nat.digits 10 x).sum = x) :
  x = 18
```

**Formal statement B**

```lean
theorem X (a b : ℕ) (h₀ : 1 ≤ a ∧ a ≤ 9 ∧ b ≤ 9)
  (h₁ : 10 * a + b = 2 * (a + b)) : 10 * a + b = 18
```

## t082

**Informal statement**

If $\displaystyle\frac{n+5}{n-3} = 2$ what is the value of $n$? Show that it is 11.

**Formal statement A**

```lean
theorem X (n : ℝ) (h₀ : n ≠ 3) (h₁ : (n + 5) / (n - 3) = 2) : n = 11
```

**Formal statement B**

```lean
theorem X (n : ℝ) (h₁ : (n + 5) / (n - 3) = 2) : n = 11
```

## t103

**Informal statement**

If $f(x)=x^3-8$, what is $f^{-1}(f(f^{-1}(19)))$? Show that it is 3.

**Formal statement A**

```lean
theorem X 
  (f : ℝ → ℝ)
  (h₀: f = fun x ↦ x ^ 3 - 8) :
  Function.invFun f (f (Function.invFun f 19)) = 3
```

**Formal statement B**

```lean
theorem X (σ : Equiv ℝ ℝ) (h : ∀ x, σ.1 x = x ^ 3 - 8) : σ.2 (σ.1 (σ.2 19)) = 3
```

## t266

**Informal statement**

Let $A$ be a nonempty set of real numbers which is bounded below. Let $-A$ be the set of all numbers $-x$, where $x \in A$. Prove that $\inf A=-\sup (-A)$.

**Formal statement A**

```lean
theorem X (A minus_A : Set ℝ) (hA : A.Nonempty)
  (hA_bdd_below : BddBelow A) (hminus_A : minus_A = {x | -x ∈ A}) :
  Inf A = Sup minus_A
```

**Formal statement B**

```lean
theorem X (A minus_A : Set ℝ) (hA : A.Nonempty)
  (hA_bdd_below : BddBelow A) (hminus_A : minus_A = {x | -x ∈ A}) :
  sInf A = - sSup minus_A
```

## t189

**Informal statement**

Prove that $\left(\sum_{j=1}^{n} a_{j} b_{j}\right)^{2} \leq\left(\sum_{j=1}^{n} j a_{j}{ }^{2}\right)\left(\sum_{j=1}^{n} \frac{b_{j}{ }^{2}}{j}\right)$ for all real numbers $a_{1}, \ldots, a_{n}$ and $b_{1}, \ldots, b_{n}$.

**Formal statement A**

```lean
theorem X {n : ℕ} (a b : Fin n → ℝ) :
  (∑ i, a i * b i) ^ 2 ≤ (∑ i : Fin n, i * a i ^ 2) * (∑ i, b i ^ 2 / i)
```

**Formal statement B**

```lean
theorem X {n : ℕ} (a b : Fin n → ℝ) :
  (∑ i, a i * b i) ^ 2 ≤ (∑ i : Fin n, (i + 1) * a i ^ 2) * (∑ i, b i ^ 2 / (i + 1))
```

## t258

**Informal statement**

Prove that for each positive integer $n$, the number $10^{10^{10^n}}+10^{10^n}+10^n-1$ is not prime.

**Formal statement A**

```lean
theorem X (n : ℕ) :
  ¬ Nat.Prime (10^10^10^n + 10^10^n + 10^n - 1)
```

**Formal statement B**

```lean
theorem X (n : ℕ) (hn : n > 0) :
  ¬ Nat.Prime (10^10^10^n + 10^10^n + 10^n - 1)
```

## t002

**Informal statement**

Let $f(x)=|x-p|+|x-15|+|x-p-15|$, where $0 < p < 15$. Determine the [[minimum]] value taken by $f(x)$ for $x$ in the [[interval]] $p \leq x\leq15$. Show that it is 015.

**Formal statement A**

```lean
theorem X
  (p : ℝ)
  (f : ℝ → ℝ)
  (h₀ : f = fun x => abs (x - p) + abs (x - 15) + abs (x - p - 15))
  (h₁ : 0 < p ∧ p < 15)
  (S R : Set ℝ)
  (hS : S = Set.Icc p 15)
  (hR : R = {y | ∃ x ∈ S, y = f x}) :
  IsLeast R 15
```

**Formal statement B**

```lean
theorem X (x p : ℝ) (f : ℝ → ℝ) (h₀ : 0 < p ∧ p < 15) (h₁ : p ≤ x ∧ x ≤ 15)
    (h₂ : f x = abs (x - p) + abs (x - 15) + abs (x - p - 15)) : 15 ≤ f x
```

## t017

**Informal statement**

Let $P(n)$ and $S(n)$ denote the product and the sum, respectively, of the digits
of the integer $n$. For example, $P(23) = 6$ and $S(23) = 5$. Suppose $N$ is a
two-digit number such that $N = P(N)+S(N)$. What is the units digit of $N$?

$\text{(A)}\ 2\qquad \text{(B)}\ 3\qquad \text{(C)}\ 6\qquad \text{(D)}\ 8\qquad \text{(E)}\ 9$ Show that it is (\text{E})9.

**Formal statement A**

```lean
theorem X
  (n : ℕ)
  (P S : ℕ → ℕ)
  (h₀ : P = fun x => (Nat.digits 10 x).prod)
  (h₁ : S = fun x => (Nat.digits 10 x).sum)
  (h₂ : (Nat.digits 10 n).length = 2)
  (h₃ : n = P n + S n) :
  n % 10 = 9
```

**Formal statement B**

```lean
theorem X (a b n : ℕ) (h₀ : 1 ≤ a ∧ a ≤ 9) (h₁ : 0 ≤ b ∧ b ≤ 9) (h₂ : n = 10 * a + b)
  (h₃ : n = a * b + a + b) : b = 9
```

## t265

**Informal statement**

If $r$ is rational $(r \neq 0)$ and $x$ is irrational, prove that $r+x$ is irrational.

**Formal statement A**

```lean
theorem X
  (x : ℝ) (y : ℚ) :
  ( Irrational x ) -> Irrational ( x + y )
```

**Formal statement B**

```lean
theorem X
  (x : ℝ) (y : ℚ) (hy : y ≠ 0) :
  ( Irrational x ) -> Irrational ( x + y )
```

## t036

**Informal statement**

Suppose that the roots of the polynomial $P(x)=x^3+ax^2+bx+c$ are $\cos \frac{2\pi}7,\cos \frac{4\pi}7,$ and $\cos \frac{6\pi}7$, where angles are in radians. What is $abc$?

$\textbf{(A) }{-}\frac{3}{49} \qquad \textbf{(B) }{-}\frac{1}{28} \qquad \textbf{(C) }\frac{\sqrt[3]7}{64} \qquad \textbf{(D) }\frac{1}{32}\qquad \textbf{(E) }\frac{1}{28}$ Show that it is \textbf{(D) }\frac{1}{32}.

**Formal statement A**

```lean
theorem X (a b c : ℝ) (f : ℝ → ℝ) (h₀ : ∀ x, f x = x ^ 3 + a * x ^ 2 + b * x + c)
  (h₁ : f (Real.cos (2 * Real.pi / 7)) = 0 ∧ f (Real.cos (4 * Real.pi / 7)) = 0 ∧ f (Real.cos (6 * Real.pi / 7)) = 0) :
  a * b * c = 1 / 32
```

**Formal statement B**

```lean
theorem X (a b c : ℝ) (f : ℝ → ℝ) (h₀ : ∀ x, f x = x ^ 3 + a * x ^ 2 + b * x + c)
    (h₁ :
      f ⁻¹' {0} =
        {Real.cos (2 * Real.pi / 7), Real.cos (4 * Real.pi / 7), Real.cos (6 * Real.pi / 7)}) :
    a * b * c = 1 / 32
```

## t172

**Informal statement**

Solve the congruence $5n \equiv 8 \pmod{17}$, as a residue modulo 17.  (Give an answer between 0 and 16.) Show that it is 5.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : 5 * n % 17 = 8) : n % 17 = 5
```

**Formal statement B**

```lean
theorem X : {n : ZMod 17 | 5 * n.val ≡ 8 [ZMOD 17]} = {5}
```

## t234

**Informal statement**

If $a \in C$ is such that $p(a) = 0$, where $p(x) = x^5 + \sqrt{2}x^3 + \sqrt{5}x^2 + \sqrt{7}x + \sqrt{11}$, show that $a$ is algebraic over $\mathbb{Q}$ of degree at most 80.

**Formal statement A**

```lean
theorem X {a : ℂ} {p : ℂ → ℂ}
  (hp : p = λ (x : ℂ) => x^5 + sqrt 2 * x^3 + sqrt 5 * x^2 + sqrt 7 * x + sqrt 11)
  (ha : p a = 0) :
  ∃ q : Polynomial ℂ, q ≠ 0 ∧ q.degree ≤ 80 ∧ a ∈ q.roots ∧
  ∀ n : q.support, ∃ a b : ℤ, q.coeff n = a / b
```

**Formal statement B**

```lean
theorem X {a : ℂ} {p : ℂ → ℂ}
  (hp : p = λ (x : ℂ) => x^5 + sqrt 2 * x^3 + sqrt 5 * x^2 + sqrt 7 * x + 11)
  (ha : p a = 0) :
  ∃ p : Polynomial ℂ , p.degree < 80 ∧ a ∈ p.roots ∧
  ∀ n : p.support, ∃ a b : ℤ, p.coeff n = a / b
```

## t200

**Informal statement**

Let $H$ be a subgroup of the additive group of rational numbers with the property that $1 / x \in H$ for every nonzero element $x$ of $H$. Prove that $H=0$ or $\mathbb{Q}$.

**Formal statement A**

```lean
theorem X (H : AddSubgroup ℚ) {x : ℚ}
  (hH : x ∈ H → (1 / x) ∈ H):
  H = ⊥ ∨ H = ⊤
```

**Formal statement B**

```lean
theorem X (H : AddSubgroup ℚ) {x : ℚ}
  (hH : (x ∈ H ∧ x ≠ 0) → (1 / x) ∈ H):
  H = ⊥ ∨ H = ⊤
```

## t045

**Informal statement**

What is the maximum value of $\frac{(2^t-3t)t}{4^t}$ for real values of $t?$

$\textbf{(A)}\ \frac{1}{16} \qquad\textbf{(B)}\ \frac{1}{15} \qquad\textbf{(C)}\ \frac{1}{12} \qquad\textbf{(D)}\ \frac{1}{10} \qquad\textbf{(E)}\ \frac{1}{9}$ Show that it is \textbf{(C)} \frac{1}{12}.

**Formal statement A**

```lean
theorem X
  (S : Set ℝ)
  (hS: S = {x:ℝ | ∃ t, x = (2 ^ t - 3 * t) * t / 4 ^ t}) :
  IsGreatest S (1 / 12:ℝ)
```

**Formal statement B**

```lean
theorem X (t : ℝ) : (2 ^ t - 3 * t) * t / 4 ^ t ≤ 1 / 12
```

## t048

**Informal statement**

Ms. Blackwell gives an exam to two classes. The mean of the scores of the students in the morning class is $84$, and the afternoon class's mean score is $70$. The ratio of the number of students in the morning class to the number of students in the afternoon class is $\frac{3}{4}$. What is the mean of the scores of all the students?

$\textbf{(A)} ~74 \qquad\textbf{(B)} ~75 \qquad\textbf{(C)} ~76 \qquad\textbf{(D)} ~77 \qquad\textbf{(E)} Show that it is \textbf{(C)} ~76.

**Formal statement A**

```lean
theorem X (m a : ℕ) (h₀ : 0 < m ∧ 0 < a) (h₁ : ↑m / ↑a = (3 : ℝ) / 4) :
    (84 * ↑m + 70 * ↑a) / (↑m + ↑a) = (76 : ℝ)
```

**Formal statement B**

```lean
theorem X
  (m a : ℕ)
  (gm ga : ℕ → ℝ)
  (h₀ : 0 < m ∧ 0 < a)
  (h₁ : (↑m:ℝ) / ↑a = (3 : ℝ) / 4)
  (h₂: ∑ x ∈ Finset.range m, gm x / (m:ℝ) = 84)
  (h₂: ∑ x ∈ Finset.range a, ga x / (a:ℝ) = 70) :
  (∑ x ∈ Finset.range m, gm x + ∑ x ∈ Finset.range a, ga x) / ((↑m:ℝ) + ↑a) = (76 : ℝ)
```

## t149

**Informal statement**

What is the sum of all of the positive factors of $36$? Show that it is 91.

**Formal statement A**

```lean
theorem X (S : Finset ℕ) (h₀ : ∀ n : ℕ, n ∈ S ↔ n ∣ 36) : (∑ k in S, k) = 91
```

**Formal statement B**

```lean
theorem X (S : Finset ℕ) (h₀ : ∀ n : ℕ, n ∈ S ↔ (0 < n ∧ n ∣ 36)) : (∑ k ∈ S, k) = 91
```

## t032

**Informal statement**

How many positive integers $n$ are there such that $n$ is a multiple of $5$, and the least common multiple of $5!$ and $n$ equals $5$ times the greatest common divisor of $10!$ and $n?$

$\textbf{(A) } 12 \qquad \textbf{(B) } 24 \qquad \textbf{(C) } 36 \qquad \textbf{(D) } 48 \qquad \textbf{(E) } 72$ Show that it is \textbf{(D) } 48.

**Formal statement A**

```lean
theorem X (S : Finset ℕ)
  (h₀ : ∀ n : ℕ, n ∈ S ↔ 5 ∣ n ∧ Nat.lcm 5! n = 5 * Nat.gcd 10! n) : S.card = 48
```

**Formal statement B**

```lean
theorem X (S : Finset ℕ)
  (h₀ : ∀ n : ℕ, n ∈ S ↔ 0 < n ∧ 5 ∣ n ∧ Nat.lcm 5! n = 5 * Nat.gcd 10! n) : S.card = 48
```

## t230

**Informal statement**

Let $F = \mathbb{Z}_p$ be the field of integers $\mod p$, where $p$ is a prime, and let $q(x) \in F[x]$ be irreducible of degree $n$. Show that $F[x]/(q(x))$ is a field having at exactly $p^n$ elements.

**Formal statement A**

```lean
theorem X {p n: ℕ} (hp : Nat.Prime p)
  {q : Polynomial (ZMod p)} (hq : Irreducible q) (hn : q.degree = n) :
  ∃ is_fin : Fintype $ Polynomial (ZMod p) ⧸ span ({q} : Set (Polynomial $ ZMod p)),
  @card (Polynomial (ZMod p) ⧸ span {q}) is_fin = p ^ n ∧
  IsField (Polynomial $ ZMod p)
```

**Formal statement B**

```lean
theorem X {p n: ℕ} (hp : Nat.Prime p)
  {q : Polynomial (ZMod p)} (hq : Irreducible q) (hn : q.degree = n) :
  (∃ is_fin : Fintype $ Polynomial (ZMod p) ⧸ span ({q}),
  @card (Polynomial (ZMod p) ⧸ span {q}) is_fin = p ^ n) ∧
  IsField (Polynomial (ZMod p) ⧸ span {q})
```

## t141

**Informal statement**

When the two-digit integer $``\text{AB}"$ is cubed, the value is $912,\!673$. What is $A + B$? Show that it is 16.

**Formal statement A**

```lean
theorem X
  (a b n : ℕ)
  (h₀ : Nat.digits 10 n = [b, a])
  (h₁ : n ^ 3 = 912673) : 
  a + b = 16
```

**Formal statement B**

```lean
theorem X (a b : ℕ) (h₀ : 1 ≤ a ∧ a ≤ 9 ∧ b ≤ 9)
    (h₁ : (10 * a + b) ^ 3 = 912673) : a + b = 16
```

## t175

**Informal statement**

Let $a_0 = 1$. For any positive integer $n$, let $a_{n+1} = \prod_{k = 1}^n a_k + 4$. Show that for any positive integer $n$, $a_n - \sqrt{a_{n+1}} = 2$.

**Formal statement A**

```lean
theorem X (a : ℕ → ℝ) (h₀ : a 0 = 1)
  (h₁ : ∀ n, a (n + 1) = (∏ k in Finset.range (n + 1), a k) + 4) :
  ∀ n ≥ 1, a n - Real.sqrt (a (n + 1)) = 2
```

**Formal statement B**

```lean
theorem X (a : ℕ → ℕ) (h₀ : a 0 = 1)
  (h₁ : ∀ n, a (n + 1) = (∏ k ∈ Finset.range (n + 1), a k) + 4) :
  ∀ n ≥ 1, a n - Real.sqrt (a (n + 1)) = 2
```

## t042

**Informal statement**

The product of three consecutive positive integers is $8$ times their sum. What is the sum of their [[perfect square|squares]]?

$\mathrm{(A)}\ 50
\qquad\mathrm{(B)}\ 77
\qquad\mathrm{(C)}\ 110
\qquad\mathrm{(D)}\ 149
\qquad\mathrm{(E)}\ 194$ Show that it is \mathrm{ (B)}\ 77.

**Formal statement A**

```lean
theorem X (a b c : ℕ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c) (h₁ : b = a + 1) (h₂ : c = b + 1)
    (h₃ : a * b * c = 8 * (a + b + c)) : a ^ 2 + (b ^ 2 + c ^ 2) = 77
```

**Formal statement B**

```lean
theorem X (a b c : ℕ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c) (h₁ : b = a + 1) (h₂ : c = b + 1)
  (h₃ : a * b * c = 8 * (a + b + c)) : a ^ 2 + b ^ 2 + c ^ 2 = 77
```

## t065

**Informal statement**

Show that for positive integer $n$, $\sum_{k=0}^{n-1} \frac{1}{(k+1)(k+2)} = \frac{n}{n+1}$.

**Formal statement A**

```lean
theorem X (n : ℕ) (hn₀: 0 < n):
  (∑ k ∈ Finset.range n, (1 : ℝ) / ((k + 1) * (k + 2))) = n / (n + 1)
```

**Formal statement B**

```lean
theorem X (n : ℕ) :
  (∑ k in Finset.range n, (1 : ℝ) / ((k + 1) * (k + 2))) = n / (n + 1)
```

## t058

**Informal statement**

Let $a,b,c,d$ be odd integers such that $0<a<b<c<d$ and $ad=bc$. Prove that if $a+d=2^k$ and $b+c=2^m$ for some integers $k$ and $m$, then $a=1$.

**Formal statement A**

```lean
theorem X
  (a b c d k m : ℤ)
  (h₀ : 0 < a ∧ 0 < b ∧ 0 < c ∧ 0 < d)
  (h₁ : Odd a ∧ Odd b ∧ Odd c ∧ Odd d)
  (h₂ : a < b ∧ b < c ∧ c < d)
  (h₃ : a * d = b * c)
  (h₄ : a + d = (2:ℝ) ^ k)
  (h₅ : b + c = (2:ℝ) ^ m) :
  a = 1
```

**Formal statement B**

```lean
theorem X (a b c d k m : ℕ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c ∧ 0 < d)
    (h₁ : Odd a ∧ Odd b ∧ Odd c ∧ Odd d) (h₂ : a < b ∧ b < c ∧ c < d) (h₃ : a * d = b * c)
    (h₄ : a + d = 2 ^ k) (h₅ : b + c = 2 ^ m) : a = 1
```

## t223

**Informal statement**

Let $A$ be a normal subgroup of a group $G$, and suppose that $b \in G$ is an element of prime order $p$, and that $b \not\in A$. Show that $A \cap (b) = (e)$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] (A : Subgroup G)
  [A.Normal] {b : G} (hp : Nat.Prime (orderOf b)) :
  A ⊓ (Subgroup.closure {b}) = ⊥
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] (A : Subgroup G)
  [A.Normal] {b : G} (hb : b ∉ A) (hp : Nat.Prime (orderOf b)) :
  A ⊓ (Subgroup.closure {b}) = ⊥
```

## t161

**Informal statement**

Suppose $a$ and $b$ are positive integers such that the units digit of $a$ is $2$, the units digit of $b$ is $4$, and the greatest common divisor of $a$ and $b$ is $6$.

What is the smallest possible value of the least common multiple of $a$ and $b$? Show that it is 108.

**Formal statement A**

```lean
theorem X (a b : ℕ) (h₀ : 0 < a ∧ 0 < b) (h₁ : a % 10 = 2) (h₂ : b % 10 = 4)
    (h₃ : Nat.gcd a b = 6) : 108 ≤ Nat.lcm a b
```

**Formal statement B**

```lean
theorem X
  (S : Set ℕ)
  (hS : S = {n | ∃ a b:ℕ, 0 < a ∧ 0 < b ∧ a % 10 = 2 ∧ b % 10 = 4 ∧ Nat.gcd a b = 6 ∧ n = Nat.lcm a b}) :
  IsLeast S 108
```

## t038

**Informal statement**

The sum of two natural numbers is $17{,}402$. One of the two numbers is divisible by $10$. If the units digit of that number is erased, the other number is obtained. What is the difference of these two numbers?

$\textbf{(A)} ~10{,}272\qquad\textbf{(B)} ~11{,}700\qquad\textbf{(C)} ~13{,}362\qquad\textbf{(D)} ~14{,}238\qquad\textbf{(E)} Show that it is \textbf{(D)} ~14{,}238.

**Formal statement A**

```lean
theorem X (x y : ℕ) (h₀ : x + y = 17402) (h₁ : 10 ∣ x) (h₂ : x / 10 = y) :
    ↑x - ↑y = (14238 : ℤ)
```

**Formal statement B**

```lean
theorem X
  (x y : ℕ)
  (h₀ : x + y = 17402)
  (h₁ : 10 ∣ x)
  (h₂ : (Nat.digits 10 x).drop 1 = Nat.digits 10 y)
  (h₂ : x / 10 = y) :
  abs ((↑x:ℤ) - ↑y) = (14238 : ℤ)
```

## t119

**Informal statement**

Jasmine drank 1.5 pints of water on the first 3 miles of her hike. If she continued at this rate, how many pints of water would she drink in the next 10 miles? Show that it is 5.

**Formal statement A**

```lean
theorem X (x : ℝ) (h₀ : 3 / 2 / 3 = x / 10) : x = 5
```

**Formal statement B**

```lean
theorem X
  (x : ℝ)
  (h₀: x * 3 = 3 / (2:ℝ)):
  x * 10 = 5
```

## t117

**Informal statement**

Find the integer that lies between $\sqrt[3]{-45}$ and $\sqrt[3]{-101}$. Show that it is -4.

**Formal statement A**

```lean
theorem X (x y : ℝ) (n : ℤ) (h₀ : x ^ 3 = -45) (h₁ : y ^ 3 = -101) (h₂ : x < n)
  (h₃ : ↑n < y) : n = -4
```

**Formal statement B**

```lean
theorem X (n : ℤ) (h₀ : -(45 ^ (1/3)) ≤ n) (h₁ : n ≤ -(101 ^ (1/3))) : n = -4
```

## t087

**Informal statement**

The graph of $y=ax^2 + bx + c$ is a parabola with vertical axis of symmetry.  The vertex of this parabola is $(2,3)$ and the parabola contains the point $(4,4)$.  Find the value of $y$ when $x=6$. Show that it is 7.

**Formal statement A**

```lean
theorem X 
  (a b c : ℝ) 
  (f : ℝ → ℝ) 
  (h₀ : ∀ x, f x = a * (x) ^ 2 + b * x + c)
  (h₁: IsExtrOn f Set.univ 2)
  (h₂: f 2 = 3)
  (h₃ : f 4 = 4) :
  f 6 = 7
```

**Formal statement B**

```lean
theorem X (a : ℝ) (f : ℝ → ℝ) (h₀ : ∀ x, f x = a * (x - 2) ^ 2 + 3) (h₁ : f 4 = 4) :
  f 6 = 7
```

## t286

**Informal statement**

Suppose $f$ is continuous in a region $\Omega$. Prove that any two primitives of $f$ (if they exist) differ by a constant.

**Formal statement A**

```lean
theorem X
  (f F₁ F₂ : ℂ → ℂ) (Ω : Set ℂ) (h0 : Nonempty Ω) (h1 : IsOpen Ω) (h2 : IsConnected Ω) (hf : ContinuousOn f Ω)
  (hF₁ : DifferentiableOn ℂ F₁ Ω) (hF₂ : DifferentiableOn ℂ F₂ Ω)
  (hdF₁ : ∀ x ∈ Ω, deriv F₁ x = f x) (hdF₂ : ∀ x ∈ Ω, deriv F₂ x = f x)
  : ∃ c : ℂ, ∀ x, F₁ x = F₂ x + c
```

**Formal statement B**

```lean
theorem X
  (f F₁ F₂ : ℂ → ℂ) (Ω : Set ℂ) (h1 : IsOpen Ω) (h2 : IsConnected Ω)
  (hF₁ : DifferentiableOn ℂ F₁ Ω) (hF₂ : DifferentiableOn ℂ F₂ Ω)
  (hdF₁ : ∀ x ∈ Ω, deriv F₁ x = f x) (hdF₂ : ∀ x ∈ Ω, deriv F₂ x = f x)
  : ∃ c : ℂ, ∀ x, F₁ x = F₂ x + c
```
