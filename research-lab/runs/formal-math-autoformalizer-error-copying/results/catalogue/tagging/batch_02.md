# Tagging batch 02 (40 items)

## t097

**Informal statement**

What is the largest number $c$ such that $2x^2+5x+c=0$ has at least one real solution? Express your answer as a common fraction. Show that it is \frac{25}{8}.

**Formal statement A**

```lean
theorem X (c : ℝ) (f : ℝ → ℝ) (h₀ : ∀ x, f x = 2 * x ^ 2 + 5 * x + c)
  (h₁ : ∃ x, f x ≤ 0) : c ≤ 25 / 8
```

**Formal statement B**

```lean
theorem X
  (S : Set ℝ)
  (hS : S = {c | ∃ x:ℝ, 2 * x ^ 2 + 5 * x + c = 0}) :
  IsGreatest S (25/8:ℝ)
```

## t030

**Informal statement**

There are integers $a, b,$ and $c,$ each greater than $1,$ such that

$\sqrt[a]{N\sqrt[b]{N\sqrt[c]{N}}} = \sqrt[36]{N^{25}}$

for all $N \neq 1$. What is $b$?

$\textbf{(A) } 2 \qquad \textbf{(B) } 3 \qquad \textbf{(C) } 4 \qquad \textbf{(D) } 5 \qquad \textbf{(E) } 6$ Show that it is \textbf{(B) } 3..

**Formal statement A**

```lean
theorem X (a b c : ℕ) (h₁ : 1 < a ∧ 1 < b ∧ 1 < c)
  (h₂ : ∀ n:NNReal, n ≠ 1 → (n * (n * n ^ (1 / c)) ^ (1 / b)) ^ (1 / a) = (n ^ 25) ^ (1 / 36)) : b = 3
```

**Formal statement B**

```lean
theorem X (a b c : ℕ) (n : NNReal) (h₀ : n ≠ 1) (h₁ : 1 < a ∧ 1 < b ∧ 1 < c)
  (h₂ : (n * (n * n ^ (1 / c)) ^ (1 / b)) ^ (1 / a) = (n ^ 25) ^ (1 / 36)) : b = 3
```

## t227

**Informal statement**

If $a^2 = 0$ in $R$, show that $ax + xa$ commutes with $a$.

**Formal statement A**

```lean
theorem X {R : Type*} [Ring R] (a x : R)
  (h : a ^ 2 = 0) : a * (a * x + x * a) = (x + x * a) * a
```

**Formal statement B**

```lean
theorem X {R : Type*} [Ring R] (a x : R)
  (h : a ^ 2 = 0) : a * (a * x + x * a) = (a * x + x * a) * a
```

## t198

**Informal statement**

Let $G$ be any group. Prove that the map from $G$ to itself defined by $g \mapsto g^{-1}$ is a homomorphism if and only if $G$ is abelian.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] (f : G → G)
  (hf : f = λ g => g⁻¹) :
  ∀ x y : G, f x * f y = f (x*y) ↔ ∀ x y : G, x*y = y*x
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] (f : G → G)
  (hf : f = λ g => g⁻¹) :
  (∀ x y : G, f x * f y = f (x*y)) ↔ ∀ x y : G, x*y = y*x
```

## t288

**Informal statement**

Prove that if $f$ is holomorphic in the unit disc, bounded and not identically zero, and $z_{1}, z_{2}, \ldots, z_{n}, \ldots$ are its zeros $\left(\left|z_{k}\right|<1\right)$, then $\sum_{n}\left(1-\left|z_{n}\right|\right)<\infty$.

**Formal statement A**

```lean
theorem X (f : ℂ → ℂ) (hf : DifferentiableOn ℂ f (ball 0 1))
  (hb : Bornology.IsBounded (Set.range f)) (h0 : f ≠ 0) (zeros : ℕ → ℂ)
  (hz : Set.range zeros = {z | f z = 0 ∧ z ∈ (ball (0 : ℂ) 1)}) :
  ∃ (l : ℝ), Tendsto (λ n => (∑ i in range n, (1 - abs (zeros i)))) atTop (𝓝 l)
```

**Formal statement B**

```lean
theorem X (f : ℂ → ℂ) (hf : DifferentiableOn ℂ f (ball 0 1))
  (hb : Bornology.IsBounded (Set.range f)) (h0 : f ≠ 0) (zeros : ℕ → ℂ) (hz : ∀ n, f (zeros n) = 0)
  (hzz : Set.range zeros = {z | f z = 0 ∧ z ∈ (ball (0 : ℂ) 1)}) :
  ∃ (z : ℂ), Tendsto (λ n => (∑ i in range n, (1 - zeros i))) atTop (𝓝 z)
```

## t250

**Informal statement**

Show that if $X$ has a countable dense subset, every collection of disjoint open sets in $X$ is countable.

**Formal statement A**

```lean
theorem X {X : Type*} [TopologicalSpace X]
  (h : ∃ (s : Set X), Countable s ∧ Dense s) (U : Set (Set X))
  (hU : ∀ (x y : Set X), x ∈ U → y ∈ U → x ≠ y → x ∩ y = ∅)
  (hUopen : ∀ (u : Set X), u ∈ U → IsOpen u) :
  Countable U
```

**Formal statement B**

```lean
theorem X {X : Type*} [TopologicalSpace X]
  (h : ∃ (s : Set X), Countable s ∧ Dense s) (U : Set (Set X))
  (hU : ∀ (x y : Set X), x ∈ U → y ∈ U → x ≠ y → x ∩ y = ∅) :
  Countable U
```

## t073

**Informal statement**

Today a father's age is five times his son's age. Exactly three years ago, the sum of their ages was 30. How old is the son today? Show that it is 6.

**Formal statement A**

```lean
theorem X (f s : ℕ) (h₁ : 5 * s = f)
  (h₂ : (f - 3) + (s - 3) = 30) : s = 6
```

**Formal statement B**

```lean
theorem X (x y : ℕ) (h₀ : 0 < x ∧ 0 < y) (h₁ : 5 * x = y)
    (h₂ : ↑x - (3 : ℤ) + (y - (3 : ℤ)) = 30) : x = 6
```

## t090

**Informal statement**

If a snack-size tin of peaches has $40$ calories and is $2\%$ of a person's daily caloric requirement, how many calories fulfill a person's daily caloric requirement? Show that it is 2000.

**Formal statement A**

```lean
theorem X (x : ℝ) (h₀ : x / 50 = 40) : x = 2000
```

**Formal statement B**

```lean
theorem X (calories_tin : ℕ) (daily_requirement : ℕ) (h : calories_tin = 40) (h2 : calories_tin = daily_requirement * (2 / 100 : ℝ)) : daily_requirement = 2000
```

## t209

**Informal statement**

Prove that there exists a normal subgroup that is not characteristic.

**Formal statement A**

```lean
theorem X :
  ∃ (G : Type*) (hG : Group G) (H : @Subgroup G hG), @Characteristic G hG H  ∧ ¬ @Normal G hG H
```

**Formal statement B**

```lean
theorem X :
  ∃ (G : Type*) (hG : Group G) (H : @Subgroup G hG), @Normal G hG H ∧ ¬ @Characteristic G hG H
```

## t068

**Informal statement**

Find the radius of the circle with equation $x^2 + 8x + y^2 - 6y = 0$. Show that it is 5.

**Formal statement A**

```lean
theorem X
  (x y : ℝ)
  (h₀ : x ^ 2 + 8 * x + y ^ 2 - 6 * y = 0) :
  ∃ a b r:ℝ, 0 < r ∧ (x + a) ^ 2 + (y + b) ^ 2 = r ^ 2 ∧ r = 5
```

**Formal statement B**

```lean
theorem X (x y : ℝ) (h₀ : x ^ 2 + 8 * x + y ^ 2 - 6 * y = 0) :
    (x + 4) ^ 2 + (y - 3) ^ 2 = 5 ^ 2
```

## t136

**Informal statement**

Convert $852_9$ to base 10. Show that it is 695.

**Formal statement A**

```lean
theorem X : 8 * 9 ^ 2 + 5 * 9 + 2 = 695
```

**Formal statement B**

```lean
theorem X
  (x : ℕ)
  (h₀ : Nat.digits 9 x = [2, 5, 8]):
  x = 695
```

## t254

**Informal statement**

Let $\|\cdot\|$ be any norm on $\mathbb{R}^{m}$ and let $B=\left\{x \in \mathbb{R}^{m}:\|x\| \leq 1\right\}$. Prove that $B$ is compact.

**Formal statement A**

```lean
theorem X (m : ℕ) {X : Type*} [NormedSpace ℝ ((Fin m) → ℝ)] :
  IsCompact (Metric.closedBall 0 1)
```

**Formal statement B**

```lean
theorem X (m : ℕ) [NormedSpace ℝ ((Fin m) → ℝ)] :
  IsCompact (Metric.closedBall (0 : EuclideanSpace ℝ (Fin m)) 1)
```

## t089

**Informal statement**

What is the sixth term in the geometric sequence $\frac{27}{125}, \frac{9}{25}, \frac{3}{5},\ldots$?  Express your answer as a common fraction. Show that it is \frac{25}{9}.

**Formal statement A**

```lean
theorem X (d : ℝ) (h₀ : 27 / 125 * d = 9 / 25) : 3 / 5 * d ^ 3 = 25 / 9
```

**Formal statement B**

```lean
theorem X
  (a : ℕ → ℚ)
  (d : ℚ)
  (h₀: ∀ n, a (n + 1) = a n * d)
  (h₁: a 0 = 27 / 125)
  (h₂: a 1 = 9 / 25)
  (h₃: a 2 = 3 / 5) :
  a 5 = 25 / 9
```

## t193

**Informal statement**

Let $x$ and $y$ be elements of $G$. Prove that $xy=yx$ if and only if $y^{-1}xy=x$ if and only if $x^{-1}y^{-1}xy=1$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G]
  (x y : G) : (x * y = y * x ↔ y⁻¹ * x * y = x) ∧ (y⁻¹ * x * y = x ↔ x⁻¹ * y⁻¹ * x * y = 1)
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G]
  (x y : G) : (x * y = y * x ↔ y⁻¹ * x * y = x) ↔ (x⁻¹ * y⁻¹ * x * y = 1)
```

## t195

**Informal statement**

Prove that the addition of residue classes $\mathbb{Z}/n\mathbb{Z}$ is associative.

**Formal statement A**

```lean
theorem X (n : ℤ) :
  ∀ (a b c : ℤ), (a+b)+c ≡ a+(b+c) [ZMOD n]
```

**Formal statement B**

```lean
theorem X (n : ℕ) : 
  ∀ (x y z : ZMod n), (x + y) + z = x + (y + z)
```

## t093

**Informal statement**

Three plus the reciprocal of a number equals 7 divided by that number.  What is the number? Show that it is 2.

**Formal statement A**

```lean
theorem X (x : ℝ) (h₁ : 3 + 1 / x = 7 / x) : x = 2
```

**Formal statement B**

```lean
theorem X (x : ℝ) (h₀ : x ≠ 0) (h₁ : 3 + 1 / x = 7 / x) : x = 2
```

## t282

**Informal statement**

Suppose (a) $f$ is continuous for $x \geq 0$, (b) $f^{\prime}(x)$ exists for $x>0$, (c) $f(0)=0$, (d) $f^{\prime}$ is monotonically increasing. Put $g(x)=\frac{f(x)}{x} \quad(x>0)$ and prove that $g$ is monotonically increasing.

**Formal statement A**

```lean
theorem X
  {f : ℝ → ℝ}
  (hf1 : ContinuousOn f (Set.Ici 0))
  (hf2 : DifferentiableOn ℝ f (Set.Ioi 0))
  (hf3 : f 0 = 0)
  (hf4 : MonotoneOn (deriv f) (Set.Ioi 0)) :
  MonotoneOn (λ x => f x / x) (Set.Ioi 0)
```

**Formal statement B**

```lean
theorem X
  {f : ℝ → ℝ}
  (hf1 : Continuous f)
  (hf2 : ∀ x, DifferentiableAt ℝ f x)
  (hf3 : f 0 = 0)
  (hf4 : Monotone (deriv f)) :
  MonotoneOn (λ x => f x / x) (Set.Ioi 0)
```

## t269

**Informal statement**

Prove that every closed set in a separable metric space is the union of a (possibly empty) perfect set and a set which is at most countable.

**Formal statement A**

```lean
theorem X (X : Type*) [MetricSpace X] [SeparableSpace X]
  (A : Set X) (hA : IsClosed A) :
  ∃ P₁ P₂ : Set X, A = P₁ ∪ P₂ ∧ Perfect P₁ ∧ Set.Countable P₂
```

**Formal statement B**

```lean
theorem X (X : Type*) [MetricSpace X] [SeparableSpace X]
  (A : Set X) (hA : IsClosed A) :
  ∃ P₁ P₂ : Set X, A = P₁ ∪ P₂ ∧
  IsClosed P₁ ∧ P₁ = {x | ClusterPt x (𝓟 P₁)} ∧
  Set.Countable P₂
```

## t071

**Informal statement**

What value of $x$ will give the minimum value for $x^2- 14x + 3$? Show that it is 7.

**Formal statement A**

```lean
theorem X
  (f : ℝ → ℝ)
  (hf: f = fun x => x^2 - 14 * x + 3) :
  IsMinOn f (Set.univ) 7
```

**Formal statement B**

```lean
theorem X (x : ℝ) : x ^ 2 - 14 * x + 3 ≥ 7 ^ 2 - 14 * 7 + 3
```

## t052

**Informal statement**

Let $a$ and $b$ be real numbers for which the equation
$x^4 + ax^3 + bx^2 + ax + 1 = 0$
has at least one real solution. For all such pairs $(a, b)$, find the minimum value of $a^2 + b^2$.

**Formal statement A**

```lean
theorem X (a b : ℝ) (h₀ : ∃ x, x ^ 4 + a * x ^ 3 + b * x ^ 2 + a * x + 1 = 0) :
  4 / 5 ≤ a ^ 2 + b ^ 2
```

**Formal statement B**

```lean
theorem X
  (S : Set (ℝ × ℝ))
  (hS : S = {(a, b) | ∃ x : ℝ, x ^ 4 + a * x ^ 3 + b * x ^ 2 + a * x + 1 = 0}) :
  IsLeast {z | ∃ a b : ℝ, (a, b) ∈ S ∧ z = a ^ 2 + b ^ 2} (4 / 5)
```

## t219

**Informal statement**

Let $R$ be an integral domain. Prove that if the following two conditions hold then $R$ is a Principal Ideal Domain: (i) any two nonzero elements $a$ and $b$ in $R$ have a greatest common divisor which can be written in the form $r a+s b$ for some $r, s \in R$, and (ii) if $a_{1}, a_{2}, a_{3}, \ldots$ are nonzero elements of $R$ such that $a_{i+1} \mid a_{i}$ for all $i$, then there is a positive integer $N$ such that $a_{n}$ is a unit times $a_{N}$ for all $n \geq N$.

**Formal statement A**

```lean
theorem X {R : Type*} [Ring R][NoZeroDivisors R]
  [CancelCommMonoidWithZero R] [GCDMonoid R]
  (h1 : ∀ a b : R, a ≠ 0 → b ≠ 0 → ∃ r s : R, gcd a b = r*a + s*b)
  (h2 : ∀ a : ℕ → R, (∀ i j : ℕ, i < j → a i ∣ a j) →
  ∃ N : ℕ, ∀ n ≥ N, ∃ u : R, IsUnit u ∧ a n = u * a N) :
  IsPrincipalIdealRing R
```

**Formal statement B**

```lean
theorem X {R : Type*} [CommRing R] [IsDomain R] [GCDMonoid R]
  (h1 : ∀ a b : R, a ≠ 0 → b ≠ 0 → ∃ r s : R, gcd a b = r*a + s*b)
  (h2 : ∀ a : ℕ → R, (∀ i : ℕ, a i ≠ 0 ∧ a (i + 1) ∣ a i) →
  ∃ N : ℕ, ∀ n ≥ N, ∃ u : R, IsUnit u ∧ a n = u * a N) :
  IsPrincipalIdealRing R
```

## t001

**Informal statement**

Let $x$, $y$ and $z$ all exceed $1$ and let $w$ be a positive number such that $\log_x w = 24$, $\log_y w = 40$ and $\log_{xyz} w = 12$. Find $\log_z w$. Show that it is 060.

**Formal statement A**

```lean
theorem X
  (x y z w : ℕ)
  (ht : 1 < x ∧ 1 < y ∧ 1 < z)
  (hw : 0 < w)
  (h0 : Real.logb x w = 24)
  (h1 : Real.logb y w = 40)
  (h2 : Real.logb (x * y * z) w = 12) :
  Real.logb z w = 60
```

**Formal statement B**

```lean
theorem X (x y z w : ℕ) (ht : 1 < x ∧ 1 < y ∧ 1 < z) (hw : 0 ≤ w)
    (h0 : Real.log w / Real.log x = 24) (h1 : Real.log w / Real.log y = 40)
    (h2 : Real.log w / Real.log (x * y * z) = 12) : Real.log w / Real.log z = 60
```

## t088

**Informal statement**

What is the sum of the two values of $x$ for which $(x+3)^2 = 121$? Show that it is -6.

**Formal statement A**

```lean
theorem X (S : Finset ℝ) (h₀ : ∀ x : ℝ, x ∈ S ↔ (x + 3) ^ 2 = 121) :
    (∑ k in S, k) = -6
```

**Formal statement B**

```lean
theorem X
  (S : Finset ℝ)
  (h₀ : ∀ x : ℝ, x ∈ S ↔ (x + 3) ^ 2 = 121) :
  (∑ k ∈ S, k) = -6 ∧ S.card = 2
```

## t242

**Informal statement**

Show that $x^{4} \equiv 2(p)$ has a solution for $p \equiv 1(4)$ iff $p$ is of the form $A^{2}+64 B^{2}$.

**Formal statement A**

```lean
theorem X {p : ℕ} (hp : p.Prime) (hp1 : p ≡ 1 [MOD 4]):
  (∃ x, x^4 ≡ 2 [MOD p]) ↔ ∃ A B, p = A^2 + 64*B^2
```

**Formal statement B**

```lean
theorem X {p : ℕ} (hp : p.Prime) (hp1 : p ≡ 1 [MOD 4]):
  ∃ x, x^4 ≡ 2 [MOD p] ↔ ∃ A B, p = A^2 + 64*B^2
```

## t238

**Informal statement**

Prove that $1^{k}+2^{k}+\cdots+(p-1)^{k} \equiv 0(p)$ if $p-1 \nmid k$ and $-1(p)$ if $p-1 \mid k$.

**Formal statement A**

```lean
theorem X {p : ℕ} (hp : p.Prime) (k s: ℕ)
  (hs : s = ∑ n : Fin (p-1), (n + 1 : ℕ) ^ k) :
  ((¬ p - 1 ∣ k) → s ≡ 0 [MOD p]) ∧ (p - 1 ∣ k → s ≡ -1 [ZMOD p])
```

**Formal statement B**

```lean
theorem X {p : ℕ} (hp : p.Prime) (k s: ℕ)
  (s := ∑ n : Fin p, (n : ℕ) ^ k) :
  ((¬ p - 1 ∣ k) → s ≡ 0 [MOD p]) ∧ (p - 1 ∣ k → s ≡ 0 [MOD p])
```

## t228

**Informal statement**

Let $p$ be an odd prime and let $1 + \frac{1}{2} + ... + \frac{1}{p - 1} = \frac{a}{b}$, where $a, b$ are integers. Show that $p \mid a$.

**Formal statement A**

```lean
theorem X {p : ℕ} (hp : Nat.Prime p) (hp1 : Odd p) :
  ∃ (a b : ℤ), (a / b : ℚ) = ∑ i in Finset.range p, 1 / (i + 1) → ↑p ∣ a
```

**Formal statement B**

```lean
theorem X {p : ℕ} (hp : Nat.Prime p) (hp1 : Odd p) :
  ∀ (a b : ℤ), (a / b : ℚ) = ∑ i in Finset.range (p-1), (1 / (i + 1) : ℚ) → ↑p ∣ a
```

## t261

**Informal statement**

For $j \in\{1,2,3,4\}$, let $z_{j}$ be a complex number with $\left|z_{j}\right|=1$ and $z_{j} \neq 1$. Prove that $3-z_{1}-z_{2}-z_{3}-z_{4}+z_{1} z_{2} z_{3} z_{4} \neq 0 .$

**Formal statement A**

```lean
theorem X (z : Fin 4 → ℂ) (hz0 : ∀ n, ‖z n‖ = 1)
  (hz1 : ∀ n, z n ≠ 1) :
  3 - z 0 - z 1 - z 2 - z 3 + (z 0) * (z 1) * (z 2) * (z 3) ≠ 0
```

**Formal statement B**

```lean
theorem X (z : Fin 4 → ℂ) (hz0 : ∀ n, ‖z n‖ < 1)
  (hz1 : ∀ n : Fin 4, z n ≠ 1) :
  3 - z 0 - z 1 - z 2 - z 3 + (z 0) * (z 1) * (z 2) * (z 3) ≠ 0
```

## t072

**Informal statement**

Together, Amy and Betty have 20 apples. Amy has three times the number of apples that Betty has. How many more apples than Betty does Amy have? Show that it is 10.

**Formal statement A**

```lean
theorem X (a b : ℕ) (h₁ : a + b = 20) (h₂ : a = 3 * b) :
  a - b = 10
```

**Formal statement B**

```lean
theorem X (a b : ℕ) (h₀ : 0 < a ∧ 0 < b) (h₁ : a + b = 20) (h₂ : a = 3 * b) :
  a - b = 10
```

## t164

**Informal statement**

A positive integer $X$ is 2 more than a multiple of 3. Its units digit is the same as the units digit of a number that is 4 more than a multiple of 5. What is the smallest possible value of $X$? Show that it is 14.

**Formal statement A**

```lean
theorem X
  (S: Set ℕ)
  (hS: S = {x | x % 3 = 2 ∧ ∃ y:ℕ, (y % 5 = 4 ∧ x % 10 = y % 10)}) :
  IsLeast S 14
```

**Formal statement B**

```lean
theorem X (x y : ℕ) (h₀ : x % 3 = 2) (h₁ : y % 5 = 4) (h₂ : x % 10 = y % 10) :
    14 ≤ x
```

## t167

**Informal statement**

The greatest common divisor of positive integers $m$ and $n$ is 8. The least common multiple of $m$ and $n$ is 112. What is the least possible value of $m+n$? Show that it is 72.

**Formal statement A**

```lean
theorem X (m n : ℕ) (h₀ : 0 < m ∧ 0 < n) (h₁ : Nat.gcd m n = 8)
    (h₂ : Nat.lcm m n = 112) : 72 ≤ m + n
```

**Formal statement B**

```lean
theorem X
  (S: Set ℕ)
  (hS : S = {x | ∃ m n, x = m + n ∧ Nat.gcd m n = 8 ∧ Nat.lcm m n = 112}):
  IsLeast S 72
```

## t217

**Informal statement**

Let $P$ be a normal Sylow $p$-subgroup of $G$ and let $H$ be any subgroup of $G$. Prove that $P \cap H$ is the unique Sylow $p$-subgroup of $H$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] [Fintype G] {p : ℕ}
  (P : Sylow p G) [hP : P.Normal] (H : Subgroup G) [Fintype H] :
  ∀ R : Sylow p H, R.toSubgroup = (H ⊓ P.toSubgroup).subgroupOf H ∧
  Nonempty (Sylow p H)
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] [Fintype G] {p : ℕ}
  (P : Sylow p G) [hP : P.Normal] (H : Subgroup G) [Fintype H] :
  (∀ R : Sylow p H, R.toSubgroup = (H ⊓ P.toSubgroup).subgroupOf H) ∧
  Nonempty (Sylow p H)
```

## t063

**Informal statement**

Show that 9 divides $10^n - 1$ for any natural number n.

**Formal statement A**

```lean
theorem X (n : ℕ) : 9 ∣ 10 ^ n - 1
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) : 9 ∣ 10 ^ n - 1
```

## t170

**Informal statement**

What is the digit in the hundredths place of the decimal equivalent of $\frac{9}{160}$? Show that it is 5.

**Formal statement A**

```lean
theorem X : (Nat.floor (100 * (9 / 160 : ℝ)) % 10 = 5)
```

**Formal statement B**

```lean
theorem X : Int.floor ((9 : ℝ) / 160 * 100) = 5
```

## t169

**Informal statement**

What is the largest negative integer $x$ satisfying $$24x \equiv 15 \pmod{1199}~?$$ Show that it is -449.

**Formal statement A**

```lean
theorem X
  (S : Set ℤ)
  (hS : S = {x | x < 0 ∧ (24 * x) ≡ 15 [ZMOD 1199]}) :
  IsGreatest S (-449:ℤ)
```

**Formal statement B**

```lean
theorem X (x : ℤ) (h₀ : x < 0) (h₁ : 24 * x % 1199 = 15) : x ≤ -449
```

## t168

**Informal statement**

Compute $29^{13} - 5^{13}$ modulo 7. Show that it is 3.

**Formal statement A**

```lean
theorem X : 29^13 - 5^13 ≡ 3 [ZMOD 7]
```

**Formal statement B**

```lean
theorem X : (29 ^ 13 - 5 ^ 13) % 7 = 3
```

## t213

**Informal statement**

Prove that a group of order 351 has a normal Sylow $p$-subgroup for some prime $p$ dividing its order.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (hG : card G = 351) :
  ∃ (p : ℕ) (P : Sylow p G), P.Normal
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] [Fintype G]
  (hG : card G = 351) :
  ∃ (p : ℕ) (P : Sylow p G), p.Prime ∧ (p ∣ card G) ∧  P.Normal
```

## t107

**Informal statement**

In an arithmetic sequence, the 7th term is 30, and the 11th term is 60. What is the 21st term of this sequence? Show that it is 135.

**Formal statement A**

```lean
theorem X
  (f : ℕ+ → ℝ)
  (h₀ : ∃ d, ∀ n, f (n + 1) = f n + d)
  (h₁ : f (7) = 30)
  (h₂ : f 11 = 60) :
  f 21 = 135
```

**Formal statement B**

```lean
theorem X (a d : ℝ) (h₀ : a + 6 * d = 30) (h₁ : a + 10 * d = 60) :
    a + 20 * d = 135
```

## t016

**Informal statement**

Two different prime numbers between $4$ and $18$ are chosen. When their sum is subtracted from their product, which of the following numbers could be obtained?

$\textbf{(A)}\ 22 \qquad\textbf{(B)}\ 60 \qquad\textbf{(C)}\ 119 \qquad\textbf{(D)}\ 180 \qquad\textbf{(E)}\ 231$ Show that it is \textbf{(C) }119.

**Formal statement A**

```lean
theorem X :
  ¬ ∃ p q : ℕ, Nat.Prime p ∧ Nat.Prime q ∧ 4 ≤ p ∧ p ≤ 18 ∧ 4 ≤ p ∧ p ≤ 18 ∧ p ≠ q ∧ ↑p * ↑q - (↑p + ↑q) = 22 ∧
  ¬ ∃ p q : ℕ, Nat.Prime p ∧ Nat.Prime q ∧ 4 ≤ p ∧ p ≤ 18 ∧ 4 ≤ p ∧ p ≤ 18 ∧ p ≠ q ∧ ↑p * ↑q - (↑p + ↑q) = 60 ∧
  ∃ p q : ℕ, Nat.Prime p ∧ Nat.Prime q ∧ 4 ≤ p ∧ p ≤ 18 ∧ 4 ≤ p ∧ p ≤ 18 ∧ p ≠ q ∧ ↑p * ↑q - (↑p + ↑q) = 119 ∧
  ¬ ∃ p q : ℕ, Nat.Prime p ∧ Nat.Prime q ∧ 4 ≤ p ∧ p ≤ 18 ∧ 4 ≤ p ∧ p ≤ 18 ∧ p ≠ q ∧ ↑p * ↑q - (↑p + ↑q) = 180 ∧
  ¬ ∃ p q : ℕ, Nat.Prime p ∧ Nat.Prime q ∧ 4 ≤ p ∧ p ≤ 18 ∧ 4 ≤ p ∧ p ≤ 18 ∧ p ≠ q ∧ ↑p * ↑q - (↑p + ↑q) = 231
```

**Formal statement B**

```lean
theorem X (p q : ℕ) (h₀ : Nat.Prime p ∧ Nat.Prime q) (h₁ : 4 ≤ p ∧ p ≤ 18)
    (h₂ : 4 ≤ q ∧ q ≤ 18) : ↑p * ↑q - (↑p + ↑q) ≠ (194 : ℕ)
```

## t074

**Informal statement**

The midpoint of the line segment between $(x,y)$ and $(-9,1)$ is $(3,-5)$. Find $(x,y)$. Show that it is (15,-11).

**Formal statement A**

```lean
theorem X (x y : ℝ)
  (h₀ : midpoint ℝ (x, y) (-9, 1) = (3, -5)) :
  x = 15 ∧ y = -11
```

**Formal statement B**

```lean
theorem X (x y : ℝ) (h₀ : 2 * 3 = x - 9) (h₁ : 2 * -5 = y + 1) : x = 15 ∧ y = -11
```

## t008

**Informal statement**

Suppose that $\sec x+\tan x=\frac{22}7$ and that $\csc x+\cot x=\frac mn,$ where $\frac mn$ is in lowest terms.  Find $m+n^{}_{}.$ Show that it is 044.

**Formal statement A**

```lean
theorem X (x : ℝ) (m : ℚ) (h₀ : 1 / Real.cos x + Real.tan x = 22 / 7)
    (h₁ : 1 / Real.sin x + 1 / Real.tan x = m) : ↑m.den + m.num = 44
```

**Formal statement B**

```lean
theorem X
  (x : ℝ) (m : ℚ)
  (h₀ : 1/Real.cos x + Real.tan x = 22/7)
  (h₁ : 1/Real.sin x + Real.cot x = m) :
  ↑m.den + m.num = 44
```
