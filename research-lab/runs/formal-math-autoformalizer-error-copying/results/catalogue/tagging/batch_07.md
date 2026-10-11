# Tagging batch 07 (9 items)

## t201

**Informal statement**

A subgroup $M$ of a group $G$ is called a maximal subgroup if $M \neq G$ and the only subgroups of $G$ which contain $M$ are $M$ and $G$. Prove that if $H$ is a proper subgroup of the finite group $G$ then there is a maximal subgroup of $G$ containing $H$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] {H : Subgroup G}
  (hH : H ≠ ⊤) :
  ∃ M : Subgroup G, M ≠ ⊤ ∧
  ∀ K : Subgroup G, M ≤ K → K = M ∨ K = ⊤ ∧
  H ≤ M
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] [Fintype G] {H : Subgroup G}
  (hH : H ≠ ⊤) :
  ∃ M : Subgroup G, M ≠ ⊤ ∧
  (∀ K : Subgroup G, M ≤ K → K = M ∨ K = ⊤) ∧
  H ≤ M
```

## t113

**Informal statement**

The sum of two numbers is 25 and their difference is 11. What is the larger of the two numbers? Show that it is 18.

**Formal statement A**

```lean
theorem X (x y : ℝ) (h₀ : x + y = 25) (h₁ : abs (x - y) = 11) : max x y = 18
```

**Formal statement B**

```lean
theorem X (x y : ℝ) (h₀ : x + y = 25) (h₁ : x - y = 11) : x = 18
```

## t035

**Informal statement**

Let $f$ be a function defined on the set of positive rational numbers with the property that $f(a\cdot b)=f(a)+f(b)$ for all positive rational numbers $a$ and $b$. Suppose that $f$ also has the property that $f(p)=p$ for every prime number $p$. For which of the following numbers $x$ is $f(x)<0$?

$\textbf{(A) }\frac{17}{32} \qquad \textbf{(B) }\frac{11}{16} \qquad \textbf{(C) }\frac79 \qquad \textbf{(D) }\frac76\qquad \textbf{(E) }\frac{25}{11}$ Show that it is \textbf{(E) }\frac{25}{11}.

**Formal statement A**

```lean
theorem X (f : ℚ → ℝ) (h₀ : ∀ x > 0, ∀ y > 0, f (x * y) = f x + f y)
    (h₁ : ∀ p, Nat.Prime p → f p = p) : f (25 /. 11) < 0
```

**Formal statement B**

```lean
theorem X
  (f : ℚ → ℝ)
  (h₀ : ∀ (x y : ℚ), 0 < x → 0 < y → f (x * y) = f x + f y)
  (h₁ : ∀ (p : ℕ), (Nat.Prime p) → f p = p) :
  f (25 / 11) < 0
```

## t271

**Informal statement**

Suppose $\left\{p_{n}\right\}$ is a Cauchy sequence in a metric space $X$, and some sequence $\left\{p_{n l}\right\}$ converges to a point $p \in X$. Prove that the full sequence $\left\{p_{n}\right\}$ converges to $p$.

**Formal statement A**

```lean
theorem X {X : Type*} [MetricSpace X]
  (p : ℕ → X) (l : ℕ+) (r : X)
  (hp : CauchySeq p)
  (hpl : Tendsto (λ n => p (l * n)) atTop (𝓝 r)) :
  Tendsto p atTop (𝓝 r)
```

**Formal statement B**

```lean
theorem X {X : Type*} [MetricSpace X]
  (p : ℕ → X) (l : ℕ) (r : X)
  (hp : CauchySeq p)
  (hpl : Tendsto (λ n => p (l * n)) atTop (𝓝 r)) :
  Tendsto p atTop (𝓝 r)
```

## t022

**Informal statement**

Let $f(x)= \sqrt{ax^2+bx} $.  For how many [[real number | real]] values of $a$ is there at least one [[positive number | positive]] value of $ b $ for which the [[domain]] of $f $ and the [[range]] of $ f $ are the same [[set]]?

$ \mathrm{(A) \ 0 } \qquad \mathrm{(B) \ 1 } \qquad \mathrm{(C) \ 2 } \qquad \mathrm{(D) \ 3 } \qquad \mathrm{(E) \ \mathrm{infinitely \ many} }  $ Show that it is \mathrm{(B) \ 2 }.

**Formal statement A**

```lean
theorem X
  (f : ℝ → ℝ → ℝ → ℝ)
  (S : Finset ℝ)
  (h₀ : f = fun a b x ↦ Real.sqrt (a * x ^ 2 + b * x))
  (hS : S = {a | ∃ b, 0 < b ∧ Set.range (f a b) = { x | 0 ≤ f x }}):
  S.card = 2
```

**Formal statement B**

```lean
theorem X (a b : ℝ) (f : ℝ → ℝ) (h₀ : 0 < b)
  (h₁ : ∀ x, f x = Real.sqrt (a * x ^ 2 + b * x)) (h₂ : { x | 0 ≤ f x } = f '' { x | 0 ≤ f x }) :
  a = 0 ∨ a = -4
```

## t000

**Informal statement**

Suppose that $x,$ $y,$ and $z$ are three positive numbers that satisfy the equations $xyz = 1,$ $x + \frac {1}{z} = 5,$ and $y + \frac {1}{x} = 29.$ Then $z + \frac {1}{y} = \frac {m}{n},$ where $m$ and $n$ are [[relatively prime]] positive integers. Find $m + n$.


note: this is the type of problem that makes you think symmetry, but actually can be solved easily with substitution, and other normal technniques Show that it is 005.

**Formal statement A**

```lean
theorem X (x y z : ℝ) (m : ℚ) (h₀ : 0 < x ∧ 0 < y ∧ 0 < z) (h₁ : x * y * z = 1)
  (h₂ : x + 1 / z = 5) (h₃ : y + 1 / x = 29) (h₄ : z + 1 / y = m) (h₅ : 0 < m) :
  ↑m.den + m.num = 5
```

**Formal statement B**

```lean
theorem X (x y z m n : ℚ) (h₀ : 0 < x ∧ 0 < y ∧ 0 < z) (h₁ : x * y * z = 1)
  (h₂ : x + 1 / z = 5) (h₃ : y + 1 / x = 29) (h₄ : z + 1 / y = m) :
  m.num + ↑m.den = 5
```

## t025

**Informal statement**

$
\textbf{(A)}\ 5 \qquad
\textbf{(B)}\ 6 \qquad
\textbf{(C)}\ 7 \qquad
\textbf{(D)}\ 8 \qquad
\textbf{(E)}\ 9 $ Show that it is \textbf{(D)}\ 8.

**Formal statement A**

```lean
theorem X
  (S : Set ℝ)
  (hS : S = {z | ∃ x y:ℝ, abs (x + y) + abs (x - y) = 2 ∧ z = x ^ 2 - 6 * x + y ^ 2}) :
  IsGreatest S 8
```

**Formal statement B**

```lean
theorem X (x y : ℝ) (h₀ : abs (x + y) + abs (x - y) = 2) :
  x ^ 2 - 6 * x + y ^ 2 ≤ 8
```

## t004

**Informal statement**

Determine the value of $ab$ if $\log_8a+\log_4b^2=5$ and $\log_8b+\log_4a^2=7$. Show that it is 512.

**Formal statement A**

```lean
theorem X (a b : ℝ) (h₀ : Real.logb 8 a + Real.logb 4 (b ^ 2) = 5)
  (h₁ : Real.logb 8 b + Real.logb 4 (a ^ 2) = 7) : a * b = 512
```

**Formal statement B**

```lean
theorem X (a b : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) (h₀ : Real.logb 8 a + Real.logb 4 (b ^ 2) = 5)
  (h₁ : Real.logb 8 b + Real.logb 4 (a ^ 2) = 7) : a * b = 512
```

## t208

**Informal statement**

Prove that if $G$ is an abelian group of order $p q$, where $p$ and $q$ are distinct primes, then $G$ is cyclic.

**Formal statement A**

```lean
theorem X {G : Type*} [Fintype G] [CommGroup G]
  {p q : Nat.Primes} (hpq : p ≠ q) (hG : card G = p*q) :
  IsCyclic G
```

**Formal statement B**

```lean
theorem X {G : Type*} [Fintype G] [Group G]
  {p q : Nat.Primes} (hpq : p ≠ q) (hG : card G = p*q) :
  IsCyclic G
```
