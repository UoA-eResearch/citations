# Tagging batch 01 (40 items)

## t078

**Informal statement**

A line $\ell$ passes through the points $B(7,-1)$ and $C(-1,7)$.  The equation of this line can be written in the form $y=mx+b$; compute $m+b$. Show that it is 5.

**Formal statement A**

```lean
theorem X
  (m b : ℝ)
  (L : Set (EuclideanSpace ℝ (Fin 2)))
  (hL : L = {x | x 1 = m * x 0 + b})
  (B C : EuclideanSpace ℝ (Fin 2))
  (hB : B = ![7, -1])
  (hC : C = ![-1, 7]) :
  m + b = 5
```

**Formal statement B**

```lean
theorem X (m b : ℝ) (h₀ : m * 7 + b = -1) (h₁ : m * -1 + b = 7) : m + b = 5
```

## t160

**Informal statement**

If $321_{b}$ is equal to the base 10 integer 57, find $b$ given that $b>0$. Show that it is 4.

**Formal statement A**

```lean
theorem X (b : ℕ) (h₀ : 0 < b) (h₁ : 3 * b ^ 2 + 2 * b + 1 = 57) : b = 4
```

**Formal statement B**

```lean
theorem X
  (b : ℕ)
  (h₀ : 0 < b)
  (h₁ : Nat.digits b 57 = [1, 2, 3]) :
  b = 4
```

## t275

**Informal statement**

Prove that the convergence of $\Sigma a_{n}$ implies the convergence of $\sum \frac{\sqrt{a_{n}}}{n}$ if $a_n\geq 0$.

**Formal statement A**

```lean
theorem X
  (a : ℕ → ℝ)
  (h : ∃ y, (Tendsto (λ n => (∑ i in (range n), a i)) atTop (𝓝 y))) :
  ∃ y, Tendsto (λ n => (∑ i in (range n), sqrt (a i) / n)) atTop (𝓝 y)
```

**Formal statement B**

```lean
theorem X
  (a : ℕ → ℝ)
  (hnneg : ∀ n, a n ≥ 0)
  (h : ∃ y, (Tendsto (λ n => (∑ i in (range n), a i)) atTop (𝓝 y))) :
  ∃ y, Tendsto (λ n => (∑ i in (range n), sqrt (a i) / (i + 1))) atTop (𝓝 y)
```

## t165

**Informal statement**

If $n$ is a multiple of three, what is the remainder when $(n + 4) + (n + 6) + (n + 8)$ is divided by $9$? Show that it is 0.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₁ : 3 ∣ n) :
  (n + 4 + (n + 6) + (n + 8)) % 9 = 0
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) (h₁ : 3 ∣ n) :
    (n + 4 + (n + 6) + (n + 8)) % 9 = 0
```

## t257

**Informal statement**

Prove that there are unique positive integers $a, n$ such that $a^{n+1}-(a+1)^n=2001$.

**Formal statement A**

```lean
theorem X :
  ∃! a : ℕ, ∃! n : ℕ, a > 0 ∧ n > 0 ∧ a^(n+1) - (a+1)^n = 2001
```

**Formal statement B**

```lean
theorem X :
  ∃! p : ℕ × ℕ, p.1 > 0 ∧ p.2 > 0 ∧ p.1^(p.2 + 1) - (p.1 + 1)^(p.2) = 2001
```

## t100

**Informal statement**

If $ \sqrt{x+\!\sqrt{x+\!\sqrt{x+\!\sqrt{x+\cdots}}}}=9$, find $x$. Show that it is 72.

**Formal statement A**

```lean
theorem X (x : ℝ) (u : ℕ → ℝ) (h₀ : ∀ n, u (n + 1) = Real.sqrt (x + u n))
  (h₁ : Filter.Tendsto u Filter.atTop (nhds 9)) : x = 72
```

**Formal statement B**

```lean
theorem X (x : NNReal) (u : ℕ → NNReal) (h₀ : ∀ n, u (n + 1) = NNReal.sqrt (x + u n))
  (h₁ : Filter.Tendsto u Filter.atTop (𝓝 9)) : 9 = NNReal.sqrt (x + 9)
```

## t085

**Informal statement**

Write $\cfrac{\cfrac{3}{8}+\cfrac{7}{8}}{\cfrac{4}{5}}$ as a simplified fraction. Show that it is \cfrac{25}{16}.

**Formal statement A**

```lean
theorem X : ((3 : ℝ) / 8 + 7 / 8) / (4 / 5) = 25 / 16
```

**Formal statement B**

```lean
theorem X : ((3 : ℚ) / 8 + 7 / 8) / (4 / 5) = (25:ℚ) / 16
```

## t062

**Informal statement**

Show that for any real number $x$ and any natural number $n$, if $x > -1$, then $(1+nx)\leq (1+x)^n$.

**Formal statement A**

```lean
theorem X (x : ℝ) (n : ℕ) (h₀ : -1 < x) (h₁ : 0 < n) :
    1 + ↑n * x ≤ (1 + x) ^ (n : ℕ)
```

**Formal statement B**

```lean
theorem X (x : ℝ) (n : ℕ) (h₀ : -1 < x) :
  1 + (n:ℝ)* x ≤ (1+x)^n
```

## t112

**Informal statement**

What is the minimum possible value for $y$ in the equation $y = x^2 - 6x + 13$? Show that it is 4.

**Formal statement A**

```lean
theorem X (x y : ℝ) (h₀ : y = x ^ 2 - 6 * x + 13) : 4 ≤ y
```

**Formal statement B**

```lean
theorem X
  (f : ℝ → ℝ)
  (h₀ : f = fun x ↦ x ^ 2 - 6 * x + 13) :
  IsLeast (Set.range f) 4
```

## t210

**Informal statement**

Let $G$ be a group with subgroups $H$ and $K$ with $H \leq K$. Prove that if $H$ is characteristic in $K$ and $K$ is normal in $G$ then $H$ is normal in $G$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] (H K : Subgroup G)
  (hHK : H ≤ K) [hHK1 : (H.subgroupOf K).Characteristic] [hK : K.Normal] :
  H.Normal
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] (H K : Subgroup G)
  (hHK : H ≤ K) [hHK1 : (H.subgroupOf K).Normal] [hK : K.Normal] :
  H.Normal
```

## t274

**Informal statement**

For any two real sequences $\left\{a_{n}\right\},\left\{b_{n}\right\}$, prove that $\limsup _{n \rightarrow \infty}\left(a_{n}+b_{n}\right) \leq \limsup _{n \rightarrow \infty} a_{n}+\limsup _{n \rightarrow \infty} b_{n},$ provided the sum on the right is not of the form $\infty-\infty$.

**Formal statement A**

```lean
theorem X
  (a b : ℕ → ℝ)
  (h : limsup a + limsup b ≠ 0) :
  limsup (λ n => a n + b n) ≤ limsup a + limsup b
```

**Formal statement B**

```lean
theorem X
    (a b : ℕ → EReal)
    (hareal : ∀ n, a n ≠ ⊤ ∧ a n ≠ ⊥)
    (hbreal : ∀ n, b n ≠ ⊤ ∧ b n ≠ ⊥)
    (ha : limsup a ≠ ⊤)
    (hb : limsup b ≠ ⊥) :
    limsup (λ n => a n + b n) ≤ limsup a + limsup b
```

## t026

**Informal statement**

Define a function on the positive integers recursively by $f(1) = 2$, $f(n) = f(n-1) + 1$ if $n$ is even, and $f(n) = f(n-2) + 2$ if $n$ is odd and greater than $1$. What is $f(2017)$?

$ \textbf{(A)}\ 2017 \qquad\textbf{(B)}\ 2018 \qquad\textbf{(C)}\ 4034 \qquad\textbf{(D)}\ 4035 \qquad\textbf{(E)}\ 4036 $ Show that it is \textbf{(B)}.

**Formal statement A**

```lean
theorem X (f : ℕ+ → ℝ) (h₀ : f 1 = 2) (h₁ : ∀ (n:ℕ+), Even n → f n = f (n - 1) + 1)
  (h₂ : ∀ (n:ℕ+), 1 < n ∧ Odd (↑n:ℕ) → f n = f (n - 2) + 2) : f 2017 = 2018
```

**Formal statement B**

```lean
theorem X (f : ℕ → ℝ) (h₀ : f 1 = 2) (h₁ : ∀ n, 1 < n ∧ Even n → f n = f (n - 1) + 1)
  (h₂ : ∀ n, 1 < n ∧ Odd n → f n = f (n - 2) + 2) : f 2017 = 2018
```

## t070

**Informal statement**

What is the simplified numerical value of $\frac{a+11b}{a-b}$ if $\frac{4a+3b}{a-2b}=5$? Show that it is 2.

**Formal statement A**

```lean
theorem X (a b : ℚ)
  (h₂ : (4 * a + 3 * b) / (a - 2 * b) = 5) : (a + 11 * b) / (a - b) = 2
```

**Formal statement B**

```lean
theorem X (a b : ℝ) (h₀ : a ≠ b) (h₁ : a ≠ 2 * b)
    (h₂ : (4 * a + 3 * b) / (a - 2 * b) = 5) : (a + 11 * b) / (a - b) = 2
```

## t066

**Informal statement**

Show that for positive integer $n$, $\sum_{k=0}^{n-1} (2k + 1) = n^2$.

**Formal statement A**

```lean
theorem X (n : ℕ) : (∑ k ∈ Finset.range n, (2 * k + 1)) = n ^ 2
```

**Formal statement B**

```lean
theorem X (n : ℕ) : (∑ k in Finset.range n, 2 * k) + 1 = n ^ 2
```

## t207

**Informal statement**

Prove that if $H$ is a nontrivial normal subgroup of the solvable group $G$ then there is a nontrivial subgroup $A$ of $H$ with $A \unlhd G$ and $A$ abelian.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] [IsSolvable G]
  {H : Subgroup G} (hH : H ≠ ⊥) [H.Normal] :
  ∃ A ≤ H, A ≠ ⊥ ∧ A.Normal ∧ ∀ a b : A, a*b = b*a
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] [IsSolvable G]
  {H : Subgroup G} (hH : H ≠ ⊥) [H.Normal] :
  ∃ A ≤ H, A.Normal ∧ ∀ a b : A, a*b = b*a
```

## t268

**Informal statement**

Suppose $E\subset\mathbb{R}^k$ is uncountable, and let $P$ be the set of condensation points of $E$. Prove that at most countably many points of $E$ are not in $P$.

**Formal statement A**

```lean
theorem X (k : ℕ) (E P : Set (EuclideanSpace ℝ (Fin k)))
  (hE : ¬ Set.Countable E)
  (hP : P = {x | ∀ U ∈ 𝓝 x, ¬ Set.Countable (U ∩ E)}) :
  Set.Countable (E \ P)
```

**Formal statement B**

```lean
theorem X (k : ℕ) (E P : Set (EuclideanSpace ℝ (Fin k)))
  (hE : E.Nonempty ∧ ¬ Set.Countable E)
  (hP : P = {x | ∀ U ∈ 𝓝 x, (P ∩ E).Nonempty ∧ ¬ Set.Countable (P ∩ E)}) :
  Set.Countable (E \ P)
```

## t096

**Informal statement**

If $f(x) = \dfrac{1}{x + 2},$ what is $f(f(1))$? Show that it is \dfrac{3}{7}.

**Formal statement A**

```lean
theorem X (f : ℝ → ℝ) (h₀ : ∀ (x) (_ : x ≠ -2), f x = 1 / (x + 2)) :
    f (f 1) = 3 / 7
```

**Formal statement B**

```lean
theorem X (f : ℝ → ℝ) (h₀ : ∀ (x : ℝ), f x = 1 / (x + 2)) :
  f (f 1) = 3 / 7
```

## t263

**Informal statement**

If $k = 1$ and $\mathbf{x} \in R^{k}$, prove that there does not exist $\mathbf{y} \in R^{k}$ such that $\mathbf{y} \neq 0$ but $\mathbf{x} \cdot \mathbf{y}=0$

**Formal statement A**

```lean
theorem X
  : ∀ (x : ℝ), x ≠ 0 → ¬ ∃ (y : ℝ), y ≠ 0 ∧ x * y = 0
```

**Formal statement B**

```lean
theorem X
  : ¬ ∀ (x : ℝ), ∃ (y : ℝ), y ≠ 0 ∧ x * y = 0
```

## t182

**Informal statement**

Prove that $x^2+1$ is irreducible in $\mathbb{F}_7$

**Formal statement A**

```lean
theorem X {F : Type*} [Field F] [Fintype F] (hF : card F = 7) :
  Irreducible (X ^ 2 + 1 : Polynomial F)
```

**Formal statement B**

```lean
theorem X {F : Type*} [Field F] [Fintype F] (hF : card F = 31) :
  Irreducible (X ^ 3 - 9 : Polynomial F)
```

## t028

**Informal statement**

A sequence of numbers is defined recursively by $a_1 = 1$, $a_2 = \frac{3}{7}$, and
$a_n=\frac{a_{n-2} \cdot a_{n-1}}{2a_{n-2} - a_{n-1}}$for all $n \geq 3$ Then $a_{2019}$ can be written as $\frac{p}{q}$, where $p$ and $q$ are relatively prime positive integers. What is $p+q ?$

$\textbf{(A) } 2020 \qquad\textbf{(B) } 4039 \qquad\textbf{(C) } 6057 \qquad\textbf{(D) } 6061 \qquad\textbf{(E) } 8078$ Show that it is \textbf{(E) }8078.

**Formal statement A**

```lean
theorem X
  (a : ℕ → ℚ) (h₀ : a 1 = 1) (h₁ : a 2 = 3 / 7)
  (h₂ : ∀ n, 3 ≤ n → a n = (a (n - 2) * a (n - 1)) / (2 * a (n - 2) - a (n - 1))) :
  ↑(a 2019).den + (a 2019).num = 8078
```

**Formal statement B**

```lean
theorem X (a : ℕ → ℚ) (h₀ : a 1 = 1) (h₁ : a 2 = 3 / 7)
  (h₂ : ∀ n, a (n + 2) = a n * a (n + 1) / (2 * a n - a (n + 1))) :
  ↑(a 2019).den + (a 2019).num = 8078
```

## t061

**Informal statement**

Show that for any real numbers $a$, $b$, and $c$, we have $(ab(a^2 - b^2)) + (bc(b^2 - c^2)) + (ca(c^2 - a^2)) \leq \frac{9\sqrt{2}}{32}(a^2 + b^2 + c^2)^2$.

**Formal statement A**

```lean
theorem X (a b c : ℝ) :
  a * b * (a ^ 2 - b ^ 2) + b * c * (b ^ 2 - c ^ 2) + c * a * (c ^ 2 - a ^ 2) ≤
  9 * Real.sqrt 2 / 32 * (a ^ 2 + b ^ 2 + c ^ 2) ^ 2
```

**Formal statement B**

```lean
theorem X
  (a b c : ℝ)
  (S : Set ℝ)
  (hS : S = {M | a * b * (a ^ 2 - b ^ 2) + b * c * (b ^ 2 - c ^ 2) + c * a * (c ^ 2 - a ^ 2) ≤ M * (a ^ 2 + b ^ 2 + c ^ 2) ^ 2}) :
  IsLeast S (9 * Real.sqrt 2 / 32)
```

## t091

**Informal statement**

Simplify $\left( \frac{4}{x} \right)^{-1} \left( \frac{3x^3}{x} \right)^2 \left( \frac{1}{2x} \right)^{-3}$. Show that it is 18x^8.

**Formal statement A**

```lean
theorem X (x : ℝ) :
  (4 / x)⁻¹ * (3 * x ^ 3 / x) ^ 2 * (1 / (2 * x))⁻¹ ^ 3 = 18 * x ^ 8
```

**Formal statement B**

```lean
theorem X (x : ℝ) (h₀ : x ≠ 0) :
  (4 / x)⁻¹ * (3 * x ^ 3 / x) ^ 2 * (1 / (2 * x))⁻¹ ^ 3 = 18 * x ^ 8
```

## t176

**Informal statement**

Let $a$ and $b$ be two integer numbers. Show that the following statement is false: $a$ and $b$ are both even iff $8 \mid a^2 + b^2$.

**Formal statement A**

```lean
theorem X
  (a b : ℤ):
  ¬ (Even a ∧ Even b) ↔ 8 ∣ a ^ 2 + b ^ 2
```

**Formal statement B**

```lean
theorem X :
    ¬∀ a b : ℤ, (∃ i j, a = 2 * i ∧ b = 2 * j) ↔ ∃ k, a ^ 2 + b ^ 2 = 8 * k
```

## t166

**Informal statement**

Euler discovered that the polynomial $p(n) = n^2 - n + 41$ yields prime numbers for many small positive integer values of $n$. What is the smallest positive integer $n$ for which $p(n)$ and $p(n+1)$ share a common factor greater than $1$? Show that it is 41.

**Formal statement A**

```lean
theorem X (n : ℕ) (p : ℕ → ℕ) (h₀ : ∀ x, p x = x ^ 2 - x + 41)
    (h₁ : 1 < Nat.gcd (p n) (p (n + 1))) : 41 ≤ n
```

**Formal statement B**

```lean
theorem X
  (p : ℕ → ℕ)
  (S : Set ℕ)
  (h₀ : ∀ x, p x = x ^ 2 - x + 41)
  (h₁ : S = {n | 1 < Nat.gcd (p n) (p (n + 1))}) :
  IsLeast S 41
```

## t121

**Informal statement**

At each basketball practice last week, Jenny made twice as many free throws as she made at the previous practice.  At her fifth practice she made 48 free throws.  How many free throws did she make at the first practice? Show that it is 3.

**Formal statement A**

```lean
theorem X
  (f : ℕ+ → ℕ)
  (h₀: ∀ x:ℕ+, f (x + 1) = 2 * f (x))
  (h₁: f 5 = 48) :
  f 1 = 3
```

**Formal statement B**

```lean
theorem X (x : ℝ) (h₀ : 2 * (2 * (2 * (2 * x))) = 48) : x = 3
```

## t183

**Informal statement**

Let $p$ be a prime integer. Prove that the polynomial $x^n-p$ is irreducible in $\mathbb{Q}[x]$.

**Formal statement A**

```lean
theorem X (p : ℕ) (hp : Prime p) (n : ℕ) :
  -- p ∈ ℕ can be written as p ∈ ℚ[X]
  Irreducible (X ^ n - (p : Polynomial ℚ) : Polynomial ℚ)
```

**Formal statement B**

```lean
theorem X (p : ℕ) (hp : Prime p) (n : ℕ) (hn : n > 0) :
  Irreducible (X ^ n - (p : Polynomial ℚ) : Polynomial ℚ)
```

## t221

**Informal statement**

Prove that the quotient ring $\mathbb{Z}[i] /(1+i)$ is a field of order 2.

**Formal statement A**

```lean
theorem X {R : Type} [Ring R]
  (hR : R = (GaussianInt ⧸ span ({⟨1, 1⟩} : Set GaussianInt))) :
  IsField R ∧ ∃ finR : Fintype R, @card R finR = 2
```

**Formal statement B**

```lean
theorem X {R : Type} [Ring R]
  (hR : R = (GaussianInt ⧸ span ({⟨0, 1⟩} : Set GaussianInt))) :
  IsField R ∧ ∃ finR : Fintype R, @card R finR = 2
```

## t253

**Informal statement**

Let $(p_n)$ be a sequence and $f:\mathbb{N}\to\mathbb{N}$. The sequence $(q_k)_{k\in\mathbb{N}}$ with $q_k=p_{f(k)}$ is called a rearrangement of $(p_n)$. Show that if $f$ is an injection, the limit of a sequence is unaffected by rearrangement.

**Formal statement A**

```lean
theorem X {α : Type*} [TopologicalSpace α]
  (f : ℕ → ℕ) (p : ℕ → α) (a : α)
  (hf : Injective f) (hp : Tendsto p atTop (𝓝 a)) :
  Tendsto (λ n => p (f n)) atTop (𝓝 a)
```

**Formal statement B**

```lean
theorem X (f : ℕ → ℕ) (p : ℕ → ℝ) (a : ℝ)
  (hf : Injective f) (hp : Tendsto p atTop (𝓝 a)) :
  Tendsto (λ n => p (f n)) atTop (𝓝 a)
```

## t137

**Informal statement**

The two-digit number $``B6,''$ where $B$ is the tens digit, is the square of a positive integer. How many distinct possible values are there for $B$? Show that it is 2.

**Formal statement A**

```lean
theorem X (b : ℕ) (h₀ : b < 10)
  (h₁ : Nat.sqrt (10 * b + 6) * Nat.sqrt (10 * b + 6) = 10 * b + 6) : b = 3 ∨ b = 1
```

**Formal statement B**

```lean
theorem X
  (S : Finset ℕ)
  (hS : S = {b | ∃ x y : ℕ , Nat.digits 10 x = [6, b] ∧ 0 < y ∧ y ^ 2 = x}) :
  S.card = 2
```

## t281

**Informal statement**

Suppose $f$ is defined and differentiable for every $x>0$, and $f^{\prime}(x) \rightarrow 0$ as $x \rightarrow+\infty$. Put $g(x)=f(x+1)-f(x)$. Prove that $g(x) \rightarrow 0$ as $x \rightarrow+\infty$.

**Formal statement A**

```lean
theorem X
  {f : ℝ → ℝ}
  (hfd : DifferentiableOn ℝ f (Ioi 0))
  (hf : Tendsto (deriv f) atTop (𝓝 0)) :
  Tendsto (λ x => f (x + 1) - f x) atTop (𝓝 0)
```

**Formal statement B**

```lean
theorem X
  {f : ℝ → ℝ}
  (hfd : Differentiable ℝ f)
  (hf : Tendsto (deriv f) atTop (𝓝 0)) :
  Tendsto (λ x => f (x + 1) - f x) atTop atTop
```

## t260

**Informal statement**

Given a real number $a$, we define a sequence by $x_{0}=1$, $x_{1}=x_{2}=a$, and $x_{n+1}=2 x_{n} x_{n-1}-x_{n-2}$ for $n \geq 2$. Prove that if $x_{n}=0$ for some $n$, then the sequence is periodic.

**Formal statement A**

```lean
theorem X (a : ℝ) (x : ℕ → ℝ) (hx0 : x 0 = a)
  (hx1 : x 1 = a)
  (hxn : ∀ n : ℕ, n ≥ 2 → x (n+1) = 2*(x n)*(x (n-1)) - x (n-2))
  (h : ∃ n, x n = 0) :
  ∃ c, Function.Periodic x c
```

**Formal statement B**

```lean
theorem X (a : ℝ) (x : ℕ → ℝ) (hx0 : x 0 = 1)
  (hx1 : x 1 = a) (hx2 : x 2 = a)
  (hxn : ∀ n : ℕ, n ≥ 2 → x (n+1) = 2*(x n)*(x (n-1)) - x (n-2))
  (h : ∃ n, x n = 0) :
  ∃ c ≠ 0, Function.Periodic x c
```

## t192

**Informal statement**

Let $x$ be an element of $G$. Prove that if $|x|=n$ for some positive integer $n$ then $x^{-1}=x^{n-1}$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] {x : G} {n : ℕ}
  (hxn: orderOf x = n) :
  x⁻¹ = x ^ (n - 1 : ℤ)
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] {x : G} {n : ℕ+}
  (hxn: orderOf x = n) :
  x⁻¹ = x ^ (n - 1 : ℕ)
```

## t163

**Informal statement**

If $n$ and $k$ are positive integers such that $5<\frac nk<6$, then what is the smallest possible value of $\frac{\mathop{\text{lcm}}[n,k]}{\gcd(n,k)}$? Show that it is 22.

**Formal statement A**

```lean
theorem X (n k : ℕ) (h₀ : 0 < n ∧ 0 < k) (h₀ : (n : ℝ) / k < 6)
  (h₁ : (5 : ℝ) < n / k) : 22 ≤ Nat.lcm n k / Nat.gcd n k
```

**Formal statement B**

```lean
theorem X
  (S : Set ℕ)
  (hS : ∀ x:ℕ, x ∈ S ↔ ∃ n k :ℕ, 0 < n ∧ 0 < k ∧ (5 : ℝ) < n / k ∧ (n : ℝ) / k < 6 ∧ x = Nat.lcm n k / Nat.gcd n k) :
  IsLeast S 22
```

## t222

**Informal statement**

Prove that the ring $\mathbb{Z}\left[x_{1}, x_{2}, x_{3}, \ldots\right] /\left(x_{1} x_{2}, x_{3} x_{4}, x_{5} x_{6}, \ldots\right)$ contains infinitely many minimal prime ideals.

**Formal statement A**

```lean
theorem X {f : ℕ → MvPolynomial ℕ ℤ}
  (hf : f = λ i => MvPolynomial.X (2*i) * MvPolynomial.X (2*i+1)):
  Infinite (minimalPrimes (MvPolynomial ℕ ℤ ⧸ span (range f)))
```

**Formal statement B**

```lean
theorem X {f : ℕ → MvPolynomial ℕ ℤ}
  (hf : f = λ i => MvPolynomial.X i * MvPolynomial.X (i+1)):
  Infinite (minimalPrimes (MvPolynomial ℕ ℤ ⧸ span (range f)))
```

## t132

**Informal statement**

When 39,500 is divided by an integer $n$, the quotient is 123 and the remainder is 17. Find $n$. Show that it is 321.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : 123 * n + 17 = 39500) : n = 321
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 39500 / n = 123) (h₁: 39500 % n = 17) : n = 321
```

## t147

**Informal statement**

What is the smallest positive integer, other than $1$, that is both a perfect cube and a perfect fourth power? Show that it is 4096.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : 2 ≤ n) (h₁ : ∃ x, x ^ 3 = n) (h₂ : ∃ t, t ^ 4 = n) :
    4096 ≤ n
```

**Formal statement B**

```lean
theorem X
  (S : Set ℕ)
  (hS :  S = {n | 0 < n ∧ n ≠ 1 ∧ ∃ x, x ^ 3 = n ∧ ∃ t, t ^ 4 = n}) :
  IsLeast S 4096
```

## t054

**Informal statement**

Let $f(n)$ be a function $f: \mathbb{N}^{+}\to\mathbb{N}^{+}$. Prove that if $ f(n+1) > f(f(n)) $ for each positive integer $n$, then $f(n)=n$.

**Formal statement A**

```lean
theorem X (f : ℕ → ℕ) (h₀ : ∀ n, 0 < f n) (h₁ : ∀ n, 0 < n → f (f n) < f (n + 1)) :
    ∀ n, 0 < n → f n = n
```

**Formal statement B**

```lean
theorem X (f : ℕ+ → ℕ+) (h₀ : ∀ n, f (f n) < f (n + 1)) :
  ∀ n, f n = n
```

## t199

**Informal statement**

Let $G$ be a finite group which possesses an automorphism $\sigma$ such that $\sigma(g)=g$ if and only if $g=1$. If $\sigma^{2}$ is the identity map from $G$ to $G$, prove that $G$ is abelian.

**Formal statement A**

```lean
theorem X {G : Type*}
  [Group G] (σ : MulAut G) (hs : ∀ g : G, σ g = 1 → g = 1)
  (hs2 : ∀ g : G, σ (σ g) = g) :
  ∀ x y : G, x*y = y*x
```

**Formal statement B**

```lean
theorem X {G : Type*}
  [Group G] (σ : MulAut G) (hs : ∀ g : G, σ g = g ↔ g = 1)
  (hs2 : ∀ g : G, σ (σ g) = g) :
  ∀ x y : G, x*y = y*x
```

## t131

**Informal statement**

The greatest common divisor of two integers is $(x+3)$ and their least common multiple is $x(x+3)$, where $x$ is a positive integer. If one of the integers is 40, what is the smallest possible value of the other one? Show that it is 8.

**Formal statement A**

```lean
theorem X
  (x a : ℤ)
  (h₀ : 0 < x)
  (h₁: x = 40 ∨ a = 40)
  (Sa Sx : Set ℤ)
  (hSa : Sa = {b | Int.gcd b x = x + 3 ∧ Int.lcm b x = x * (x + 3)})
  (hSx : Sx = {y | 0 < y ∧ Int.gcd a y = y + 3 ∧ Int.lcm a y = y * (y + 3)})
  (h₂ : Nonempty Sa)
  (h₃ : Nonempty Sx) :
  IsLeast Sa 8 ∨ IsLeast Sx 8
```

**Formal statement B**

```lean
theorem X (x a : ℕ) (h₀ : 0 < x ∧ 0 < a) (h₁ : Nat.gcd a 40 = x + 3)
  (h₂ : Nat.lcm a 40 = x * (x + 3))
  (h₃ : ∀ b : ℕ, 0 < b → Nat.gcd b 40 = x + 3 ∧ Nat.lcm b 40 = x * (x + 3) → a ≤ b) : a = 8
```

## t106

**Informal statement**

If $p (x) = 2-x^2$ and $q(x) = \frac{6}{x}$, what is the value of $p (q(2))$? Show that it is -7.

**Formal statement A**

```lean
theorem X (p q : ℝ → ℝ) (h₀ : ∀ x, p x = 2 - x ^ 2)
  (h₁ : ∀ x : ℝ, q x = 6 / x) : p (q 2) = -7
```

**Formal statement B**

```lean
theorem X (p q : ℝ → ℝ) (h₀ : ∀ x, p x = 2 - x ^ 2)
    (h₁ : ∀ x : ℝ, x ≠ 0 → q x = 6 / x) : p (q 2) = -7
```
