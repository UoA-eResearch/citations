# Tagging batch 00 (40 items)

## t171

**Informal statement**

My father's age is $1222_{3}$, in base three to represent his three lower limbs -- two legs and a cane.  How old is he in base ten? Show that it is 53.

**Formal statement A**

```lean
theorem X : 1 * 3 ^ 3 + 2 * 3 ^ 2 + 2 * 3 + 2 = 53
```

**Formal statement B**

```lean
theorem X 
  (x : ℕ)
  (h₀ : Nat.digits 3 x = [2, 2, 2, 1]) :
  x = 53
```

## t144

**Informal statement**

The greatest common divisor of positive integers $m$ and $n$ is 6. The least common multiple of $m$ and $n$ is 126. What is the least possible value of $m+n$? Show that it is 60.

**Formal statement A**

```lean
theorem X (m n : ℕ) (h₀ : Nat.gcd m n = 6) (h₁ : Nat.lcm m n = 126) :
    60 ≤ m + n
```

**Formal statement B**

```lean
theorem X
  (S: Set ℕ)
  (hS: S = {x | ∃ m n:ℕ, x = m + n ∧ Nat.gcd m n = 6 ∧ Nat.lcm m n = 126}):
  IsLeast S 60
```

## t153

**Informal statement**

What is the sum of the final three digits of the integer representation of $5^{100}$? Show that it is 13.

**Formal statement A**

```lean
theorem X (a b c : ℕ)
  (h₁ : Nat.digits 10 (5 ^ 100 % 1000) = [c, b, a]) : a + b + c = 13
```

**Formal statement B**

```lean
theorem X (a b c : ℕ) (h₀ : a ≤ 9 ∧ b ≤ 9 ∧ c ≤ 9)
    (h₁ : Nat.digits 10 (5 ^ 100 % 1000) = [c, b, a]) : a + b + c = 13
```

## t080

**Informal statement**

The graphs of $y=x^4$ and $y=5x^2-6$ intersect at four points with $x$-coordinates $\pm \sqrt{m}$ and $\pm \sqrt{n}$, where $m > n$. What is $m-n$? Show that it is 1.

**Formal statement A**

```lean
theorem X
  (F G I : Set (EuclideanSpace ℝ (Fin 2)))
  (hF : F = {x | x 1 = (x 0) ^ 4})
  (hG : G = {x | x 1 = 5 * (x 0) ^ 2 - 6})
  (m n : ℝ)
  (hI : I = (F ∩ G))
  (A B C D : EuclideanSpace ℝ (Fin 2))
  (hA₀ : A = ![-Real.sqrt m, 0] ∧ A ∈ I)
  (hB₀ : B = ![Real.sqrt m, 0] ∧ B ∈ I)
  (hC₀ : C = ![-Real.sqrt n, 0] ∧ C ∈ I)
  (hD₀ : D = ![Real.sqrt n, 0] ∧ D ∈ I)
  (hmn : n < m) :
  m - n = 1
```

**Formal statement B**

```lean
theorem X (x y : ℝ) (f g : ℝ → ℝ) (h₀ : ∀ t, f t = t ^ 4)
    (h₁ : ∀ t, g t = 5 * t ^ 2 - 6) (h₂ : f x = g x) (h₃ : f y = g y) (h₄ : x ^ 2 < y ^ 2) :
    y ^ 2 - x ^ 2 = 1
```

## t204

**Informal statement**

Prove that the intersection of an arbitrary nonempty collection of normal subgroups of a group is a normal subgroup (do not assume the collection is countable).

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] (I : Type*)
  (H : I → Subgroup G) (hH : ∀ i : I, Normal (H i)) :
  Normal (⨅ (i : I), H i)
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] (I : Type*) [Nonempty I]
  (H : I → Subgroup G) (hH : ∀ i : I, Normal (H i)) :
  Normal (⨅ (i : I), H i)
```

## t220

**Informal statement**

Prove that if an integer is the sum of two rational squares, then it is the sum of two integer squares.

**Formal statement A**

```lean
theorem X {n : ℤ} {r s : ℚ}
  (h : r^2 + s^2 = n) :
  ∃ a b : ℤ, a^2 + b^2 = n
```

**Formal statement B**

```lean
theorem X {R : Type*} {n : ℤ} {r s : ℚ}
  (h : r^2 + s^2 = n) :
  ∃ a b : ℤ, a^2 + b^2 = n
```

## t095

**Informal statement**

Solve for $x$: $\frac{x+1}{x-1} = \frac{x-2}{x+2}$ Show that it is 0.

**Formal statement A**

```lean
theorem X (x : ℝ) (h₀ : (x + 1) / (x - 1) = (x - 2) / (x + 2)) : x = 0
```

**Formal statement B**

```lean
theorem X (x : ℝ) (h₀ : x ≠ 1) (h₁ : x ≠ -2)
  (h₂ : (x + 1) / (x - 1) = (x - 2) / (x + 2)) : x = 0
```

## t125

**Informal statement**

If $F(a, b, c, d) = a^b + c ^ d$, what is the value of $b$ such that $F(4, b, 2, 3) = 12$? Show that it is 1.

**Formal statement A**

```lean
theorem X
  (b : ℝ)
  (F : ℝ → ℝ → ℝ → ℝ → ℝ)
  (h₀: F = fun a b c d ↦ a ^ b + c ^ d)
  (h₁ : F 4 b 2 3 = 12) :
  b = 1
```

**Formal statement B**

```lean
theorem X (b : ℝ) (h₀ : (4 : ℝ) ^ b + 2 ^ 3 = 12) : b = 1
```

## t194

**Informal statement**

Prove that $A \times B$ is an abelian group if and only if both $A$ and $B$ are abelian.

**Formal statement A**

```lean
theorem X {A B : Type*} [Group A] [Group B] :
  (∀ x y : A × B, x*y = y*x) ↔ (∀ x y : A, x*y = y*x) ∧
  (∀ x y : B, x*y = y*x)
```

**Formal statement B**

```lean
theorem X {A B : Type*} [Group A] [Group B] :
  ∀ x y : A × B, x*y = y*x ↔ (∀ x y : A, x*y = y*x) ∧
  (∀ x y : B, x*y = y*x)
```

## t013

**Informal statement**

Let $n$ be a positive natural number. Show that $n^{1/n} \leq 2 - 1/n$.

**Formal statement A**

```lean
theorem X
  (n : ℕ)
  (hn : 0 < n) :
  (n : ℝ) ^ (1 / n:ℝ) < 2 - 1 / n
```

**Formal statement B**

```lean
theorem X (n : ℕ) : (n : ℝ) ^ ((1 : ℝ) / n) < 2 - 1 / n
```

## t162

**Informal statement**

What is the smallest integer greater than 10 that is both a perfect square and a perfect cube? Show that it is 64.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : 10 ≤ n) (h₁ : ∃ x, x ^ 2 = n) (h₂ : ∃ t, t ^ 3 = n) :
    64 ≤ n
```

**Formal statement B**

```lean
theorem X
  (S : Set ℕ)
  (hS : S = {x | 10 < x ∧ (∃ y:ℕ, y ^ 2 = x) ∧ (∃ z:ℕ, z ^ 3 = x)}):
  IsLeast S 64
```

## t190

**Informal statement**

Suppose $T \in \mathcal{L}(V)$ is self-adjoint, $\lambda \in \mathbf{F}$, and $\epsilon>0$. Prove that if there exists $v \in V$ such that $\|v\|=1$ and $\|T v-\lambda v\|<\epsilon,$ then $T$ has an eigenvalue $\lambda^{\prime}$ such that $\left|\lambda-\lambda^{\prime}\right|<\epsilon$.

**Formal statement A**

```lean
theorem X {𝕜 V : Type*} [RCLike 𝕜] [NormedAddCommGroup V]
  [InnerProductSpace 𝕜 V] [FiniteDimensional 𝕜 V]
  {T : Module.End 𝕜 V} (hT : IsSelfAdjoint T)
  {l : 𝕜} {ε : ℝ} (he : ε > 0) : (∃ v : V, ‖v‖= 1 ∧ ‖T v - l • v‖ < ε) →
  (∃ l' : T.Eigenvalues, ‖l - l'‖ < ε)
```

**Formal statement B**

```lean
theorem X {𝕜 V : Type*} [RCLike 𝕜] [NormedAddCommGroup V]
  [InnerProductSpace 𝕜 V] [FiniteDimensional 𝕜 V]
  {T : Module.End 𝕜 V} (hT : IsSelfAdjoint T)
  {l : 𝕜} {ε : ℝ} (he : ε > 0) : ∃ v : V, ‖v‖= 1 ∧ (‖T v - l • v‖ < ε →
  (∃ l' : T.Eigenvalues, ‖l - l'‖ < ε))
```

## t101

**Informal statement**

If $n = 11$, then what is $\left(\frac{1}{4}\right)^{n+1} \cdot 2^{2n}$? Show that it is \frac{1}{4}.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : n = 11) : (1 / 4) ^ (n + 1) * 2 ^ (2 * n) = 1 / 4
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : n = 11) : (1 / 4 : ℝ) ^ (n + 1) * 2 ^ (2 * n) = 1 / 4
```

## t186

**Informal statement**

Prove that the union of two subspaces of $V$ is a subspace of $V$ if and only if one of the subspaces is contained in the other.

**Formal statement A**

```lean
theorem X {F V : Type*} [AddCommGroup V] [Field F]
  [Module F V] (U W : Submodule F V):
  (∃ U' : Submodule F V, U'.carrier = ↑U ∪ ↑W) ↔ (U ≤ W ∨ W ≤ U)
```

**Formal statement B**

```lean
theorem X {F V : Type*} [AddCommGroup V] [Field F]
  [Module F V] (U W : Submodule F V):
  ∃ U' : Submodule F V, (U'.carrier = ↑U ∩ ↑W ↔ (U ≤ W ∨ W ≤ U))
```

## t060

**Informal statement**

Let $a$ and $b$ be positive integers such that $ab + 1$ divides $a^{2} + b^{2}$. Show that
$
\frac {a^{2} + b^{2}}{ab + 1}
$
is the square of an integer.

**Formal statement A**

```lean
theorem X
  (a b : ℕ)
  (h₀ : 0 < a ∧ 0 < b)
  (h₁ : (a * b + 1) ∣ (a^2 + b^2)) :
  ∃ x : ℤ, (x^2 : ℝ) = (a^2 + b^2) / (a * b + 1)
```

**Formal statement B**

```lean
theorem X (a b : ℕ) (h₀ : 0 < a ∧ 0 < b) (h₁ : a * b + 1 ∣ a ^ 2 + b ^ 2) :
  ∃ x : ℕ, (x ^ 2 : ℝ) = (a ^ 2 + b ^ 2) / (a * b + 1)
```

## t084

**Informal statement**

Suppose $f(x)$ is an invertible function, and suppose that $f(2)=f^{-1}(2)=4$.

What is the value of $f(f(2))$? Show that it is 2.

**Formal statement A**

```lean
theorem X
  (f : ℝ → ℝ)
  (h₀ : Function.Bijective f)
  (h₁ : f 2 = 4)
  (h₂ : f 2 = Function.invFun f 2) :
  f (f 2) = 2
```

**Formal statement B**

```lean
theorem X (σ : Equiv ℝ ℝ) (h : σ.1 2 = σ.2 2) : σ.1 (σ.1 2) = 2
```

## t229

**Informal statement**

Show that $(p - 1)/2$ of the numbers $1, 2, \ldots, p - 1$ are quadratic residues and $(p - 1)/2$ are quadratic nonresidues $\mod p$.

**Formal statement A**

```lean
theorem X (p : ℕ) (hp : Nat.Prime p) (hodd : p % 2 = 1) :
  (∃ S : Finset (ZMod p), 0 ∉ S ∧ S.card = (p-1)/2 ∧ ∀ q ∈ S, ∃ x : ZMod p, x^2 = q) ∧
  (∃ S : Finset (ZMod p), 0 ∉ S ∧ S.card = (p-1)/2 ∧ ∀ q ∈ S, ¬ ∃ x : ZMod p, x^2 = q)
```

**Formal statement B**

```lean
theorem X (p : ℕ) (hp : Nat.Prime p) :
  (∃ S : Finset (ZMod p), S.card = (p-1)/2 ∧ ∃ x : ZMod p, x^2 = p) ∧
  (∃ S : Finset (ZMod p), S.card = (p-1)/2 ∧ ¬ ∃ x : ZMod p, x^2 = p)
```

## t099

**Informal statement**

Calculate $\sqrt{60x} \cdot \sqrt{12x} \cdot \sqrt{63x}$ . Express your answer in simplest radical form in terms of $x$.

Note: When entering a square root with more than one character, you must use parentheses or brackets.  For example, you should enter $\sqrt{14}$ as "sqrt(14)" or "sqrt{14}". Show that it is 36x \sqrt{35x}.

**Formal statement A**

```lean
theorem X (x : ℝ) :
  Real.sqrt (60 * x) * Real.sqrt (12 * x) * Real.sqrt (63 * x) = 36 * x * Real.sqrt (35 * x)
```

**Formal statement B**

```lean
theorem X (x : NNReal) :
    Real.sqrt (60 * x) * Real.sqrt (12 * x) * Real.sqrt (63 * x) = 36 * x * Real.sqrt (35 * x)
```

## t086

**Informal statement**

Suppose that $h(x)=f^{-1}(x)$. If $h(2)=10$, $h(10)=1$ and $h(1)=2$, what is $f(f(10))$? Show that it is 1.

**Formal statement A**

```lean
theorem X (σ : Equiv ℝ ℝ) (h₀ : σ.2 2 = 10) (h₁ : σ.2 10 = 1) (h₂ : σ.2 1 = 2) :
    σ.1 (σ.1 10) = 1
```

**Formal statement B**

```lean
theorem X
  (f h : ℝ → ℝ)
  (h₀: Function.LeftInverse f h)
  (h₁ : h 2 = 10)
  (h₂ : h 10 = 1)
  (h₃ : h 1 = 2) :
  f (f 10) = 1
```

## t173

**Informal statement**

Show that for any positive integer $n$, $2$ divides $4^n$.

**Formal statement A**

```lean
theorem X (n : ℕ) (h₀ : n ≠ 0) : 2 ∣ 4 ^ n
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) : 2 ∣ 4 ^ n
```

## t055

**Informal statement**

Let $f$ be an injective function from ${1,2,3,\ldots}$ in itself. Prove that for any $n$ we have: $\sum_{k=1}^{n} f(k)k^{-2} \geq \sum_{k=1}^{n} k^{-1}.$

**Formal statement A**

```lean
theorem X (n : ℕ) (a : ℕ → ℕ) (h₀ : Function.Injective a) (h₁ : a 0 = 0) (h₂ : 0 < n) :
  (∑ k in Finset.Icc 1 n, (1 : ℝ) / k) ≤ ∑ k in Finset.Icc 1 n, (a k : ℝ) / k ^ 2
```

**Formal statement B**

```lean
theorem X
  (n : ℕ)
  (f : ℕ → ℕ)
  (h₀ : ∀ (m : ℕ), 0 < m → 0 < f m)
  (h₁ : ∀ (p q : ℕ), 0 < p → 0 < q → p ≠ q → f p ≠ f q)
  (h₂ : 0 < n) :
  (∑ k ∈ Finset.Icc 1 n, (1 : ℝ) / k) ≤ ∑ k ∈ Finset.Icc 1 n, ((f k):ℝ) / k ^ 2
```

## t126

**Informal statement**

For integers $n$, let \[f(n) = \left\{
\begin{array}{cl}
n^2 & \text{ if }n\text{ is odd}, \\
n^2 - 4n - 1 & \text{ if }n\text{ is even}.
\end{array}
\right.\]Find $f(f(f(f(f(4)))))$. Show that it is 1.

**Formal statement A**

```lean
theorem X
  (f : ℤ → ℤ) (h₀ : ∀ n, Odd n → f n = n ^ 2)
  (h₁ : ∀ n, Even n → f n = n ^ 2 - 4 * n - 1) :
  f (f (f (f (f (4))))) = 1
```

**Formal statement B**

```lean
theorem X (f : ℤ → ℤ) (h₀ : ∀ n, Odd n → f n = n ^ 2)
    (h₁ : ∀ n, Even n → f n = n ^ 2 - 4 * n - 1) : f 4 = -1
```

## t196

**Informal statement**

If $x$ is an element of infinite order in $G$, prove that the elements $x^{n}, n \in \mathbb{Z}$ are all distinct.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G] {x : G}
  (hx_inf : orderOf x = 0) (n m : ℤ) (hnm : n ≠ m) :
  x ^ n ≠ x ^ m
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G] {x : G}
  (hx_inf : orderOf x = 0) (n m : ℤ) :
  x ^ n ≠ x ^ m
```

## t069

**Informal statement**

The point $(a, b)$ lies on the line with the equation $3x + 2y = 12.$ When $a = 4$, what is the value of $b$? Show that it is 0.

**Formal statement A**

```lean
theorem X
  (a b : ℝ)
  (L : Set (EuclideanSpace ℝ (Fin 2)))
  (hL : L = { x | 3 * (x 0) + 2 * (x 1) = 12 })
  (A : EuclideanSpace ℝ (Fin 2))
  (hA₀ : A = ![a, b])
  (hA₁ : A ∈ L)
  (ha : a = 4) :
  b = 0
```

**Formal statement B**

```lean
theorem X (a b : ℝ) (h₀ : 3 * a + 2 * b = 12) (h₁ : a = 4) : b = 0
```

## t018

**Informal statement**

What is the product of all positive odd integers less than $10000$?

$\text{(A)}\ \dfrac{10000!}{(5000!)^2}\qquad \text{(B)}\ \dfrac{10000!}{2^{5000}}\qquad
\text{(C)}\ \dfrac{9999!}{2^{5000}}\qquad \text{(D)}\ \dfrac{10000!}{2^{5000} \cdot 5000!}\qquad
\text{(E)}\ \dfrac{5000!}{2^{5000}}$ Show that it is \text{(D)} \dfrac{10000!}{2^{5000} \cdot 5000!}.

**Formal statement A**

```lean
theorem X :
  Finset.prod (Finset.filter (fun (x : ℕ) => Odd x) (Finset.range 10000)) (fun (x : ℕ) => x) =
  10000! / (2 ^ (5000 : ℕ) * 5000!)
```

**Formal statement B**

```lean
theorem X :
    Finset.prod (Finset.filter (fun x => ¬Even x) (Finset.range 10000)) (id : ℕ → ℕ) =
      10000! / (2 ^ 5000 * 5000!)
```

## t225

**Informal statement**

If $G$ is a finite group, prove that there is an integer $m > 0$ such that $a^m = e$ for all $a \in G$.

**Formal statement A**

```lean
theorem X {G : Type*} [Group G]
  [Fintype G] : ∃ (m : ℕ), m > 0 ∧ ∀ (a : G), a ^ m = 1
```

**Formal statement B**

```lean
theorem X {G : Type*} [Group G]
  [Fintype G] : ∃ (m : ℕ), ∀ (a : G), a ^ m = 1
```

## t076

**Informal statement**

If $a \star b = \dfrac{\left(\dfrac{1}{b} - \dfrac{1}{a}\right)}{(a - b)}$, express $3 \star 11$ as a common fraction. Show that it is \frac{1}{33}.

**Formal statement A**

```lean
theorem X (s : ℝ → ℝ → ℝ)
    (h₀ : ∀ (x) (_ : x ≠ 0), ∀ (y) (_ : y ≠ 0), s x y = (1 / y - 1 / x) / (x - y)) :
    s 3 11 = 1 / 33
```

**Formal statement B**

```lean
theorem X
  (s : ℝ → ℝ → ℝ)
  (h₀ : ∀ x y:ℝ, s x y = (1 / y - 1 / x) / (x - y)) :
  s 3 11 = 1 / 33
```

## t174

**Informal statement**

Show that for positive integer $n$, the remainder of $3^{2^n} - 1 \equiv 2^{n+2} \mod 2^{n+3}$.

**Formal statement A**

```lean
theorem X
  (n : ℕ)
  (h₀ : 0 < n) :
  (3 ^ 2 ^ (n : ℕ) - 1) ≡ 2 ^ ((n : ℕ) + 2) [MOD 2 ^ ((n : ℕ) + 3)]
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) :
    (3 ^ 2 ^ n - 1) % 2 ^ (n + 3) = 2 ^ (n + 2)
```

## t255

**Informal statement**

Give a direct proof that the nested decreasing intersection of nonempty covering compact sets is nonempty.

**Formal statement A**

```lean
theorem X {α : Type*} [TopologicalSpace α]
  {s : ℕ → Set α}
  (hs : ∀ i, IsCompact (s i))
  (hne : ∀ i, (s i).Nonempty)
  (hs : ∀ i, (s i) ⊇ (s (i + 1))) :
  (⋂ i, s i).Nonempty
```

**Formal statement B**

```lean
theorem X {α : Type*} [TopologicalSpace α]
  {s : ℕ → Set α}
  (hs : ∀ i, IsCompact (s i))
  (hs : ∀ i, (s i).Nonempty)
  (hs : ∀ i, (s i) ⊃ (s (i + 1))) :
  (⋂ i, s i).Nonempty
```

## t252

**Informal statement**

Let $X$ be a compact Hausdorff space that is the union of the closed subspaces $X_1$ and $X_2$. If $X_1$ and $X_2$ are metrizable, show that $X$ is metrizable.

**Formal statement A**

```lean
theorem X
  (X : Type*) [TopologicalSpace X] [CompactSpace X] [T2Space X]
  (X1 X2 : Set X) (hX1 : IsClosed X1) (hX2 : IsClosed X2)
  (hX : X1 ∪ X2 = univ) (hX1m : MetrizableSpace X1)
  (hX2m : MetrizableSpace X2) : MetrizableSpace X
```

**Formal statement B**

```lean
theorem X
  (X : Type*) [TopologicalSpace X] [CompactSpace X]
  (X1 X2 : Set X) (hX1 : IsClosed X1) (hX2 : IsClosed X2)
  (hX : X1 ∪ X2 = univ) (hX1m : MetrizableSpace X1)
  (hX2m : MetrizableSpace X2) : MetrizableSpace X
```

## t236

**Informal statement**

Show that 1729 is the smallest positive integer expressible as the sum of two different integral cubes in two ways.

**Formal statement A**

```lean
theorem X {n : ℕ} (hn : ∃ x y z w : ℤ,
  x^3 + y^3 = n ∧ z^3 + w^3 = n ∧ x ≠ z ∧ x ≠ w ∧ y ≠ z ∧ y ≠ w) :
  n ≥ 1729
```

**Formal statement B**

```lean
theorem X : 1729 = sInf (fun (n : ℕ) => ∃ x y z w : ℤ,
  x^3 + y^3 = n ∧ z^3 + w^3 = n ∧ x ≠ z ∧ x ≠ w ∧ y ≠ z ∧ y ≠ w)
```

## t232

**Informal statement**

If $F$ is a field of characteristic $p \neq 0$, show that $(a + b)^m = a^m + b^m$, where $m = p^n$, for all $a, b \in F$ and any positive integer $n$.

**Formal statement A**

```lean
theorem X {p m n: ℕ} {F : Type*} [Field F]
  (hp : Nat.Prime p) (hF : CharP F p) (a b : F) (hm : m = p ^ n) :
  (a + b) ^ m = a^m + b^m
```

**Formal statement B**

```lean
theorem X {p m n: ℕ} {F : Type*} [Field F]
  (hp : p ≠ 0) (hn : n > 0)
  (hF : CharP F p) (a b : F) (hm : m = p ^ n) :
  (a + b) ^ m = a^m + b^m
```

## t197

**Informal statement**

Prove that the multiplication of residue class $\mathbb{Z}/n\mathbb{Z}$ is associative.

**Formal statement A**

```lean
theorem X (n : ℕ) (a b c : ZMod n) :
  (a * b) * c = a * (b * c)
```

**Formal statement B**

```lean
theorem X (n : ℕ) :
  ∀ (a b c : ℕ), (a * b) * c ≡ a * (b * c) [ZMOD n]
```

## t040

**Informal statement**

Let $n$ be a positive [[integer]] such that $\frac 12 + \frac 13 + \frac 17 + \frac 1n$ is an integer. Which of the following statements is '''not ''' true:

$\mathrm{(A)}\ 2\ \text{divides\ }n
\qquad\mathrm{(B)}\ 3\ \text{divides\ }n
\qquad\mathrm{(C)}$ $\ 6\ \text{divides\ }n 
\qquad\mathrm{(D)}\ 7\ \text{divides\ }n
\qquad\mathrm{(E)}\ n > 84$ Show that it is \mathrm{(E)}\ n>84.

**Formal statement A**

```lean
theorem X
  (n : ℕ)
  (h₀ : 0 < n)
  (h₁ : ((1:ℚ) / (2 : ℚ) + 1 / (3 : ℚ) + 1 / (7 : ℚ) + 1 / (↑n : ℚ)).isInt) :
  n = 42
```

**Formal statement B**

```lean
theorem X (n : ℕ) (h₀ : 0 < n) (h₁ : (1 /. 2 + 1 /. 3 + 1 /. 7 + 1 /. ↑n).den = 1) : n = 42
```

## t156

**Informal statement**

The sum of the proper divisors of 18 is 21. What is the sum of the proper divisors of 198? Show that it is 270.

**Formal statement A**

```lean
theorem X : (∑ k in Nat.properDivisors 198, k) = 270
```

**Formal statement B**

```lean
theorem X 
  (h₀: (∑ k ∈ Nat.properDivisors 18, k) = 21) : 
  (∑ k ∈ Nat.properDivisors 198, k) = 270
```

## t243

**Informal statement**

Let $A \subset X$; let $f: A \rightarrow Y$ be continuous; let $Y$ be Hausdorff. Show that if $f$ may be extended to a continuous function $g: \bar{A} \rightarrow Y$, then $g$ is uniquely determined by $f$.

**Formal statement A**

```lean
theorem X
  {X : Type*} [TopologicalSpace X] {Y : Type*} [TopologicalSpace Y] [T2Space Y]
  {A : Set X} {f : X → Y} (hf : ContinuousOn f A)
  (g : X → Y) (g_con : ContinuousOn g (closure A))
  (gExt : ∀ x : A, g x = f x) :
  ∀ (g' : X → Y), (ContinuousOn g' (closure A) ∧ (∀ x : A, g' x = f x)) → (∀ x : closure A, g x = g' x)
```

**Formal statement B**

```lean
theorem X
  {X : Type*} [TopologicalSpace X] {Y : Type*} [TopologicalSpace Y]
  [T2Space Y] {A : Set X} {f : A → Y} (hf : Continuous f)
  (g : closure A → Y)
  (g_con : Continuous g) :
  ∀ (g' : closure A → Y), Continuous g' →  (∀ (x : closure A), g x = g' x)
```

## t152

**Informal statement**

Find $9^{-1} \pmod{100}$, as a residue modulo 100.  (Give an answer between 0 and 99, inclusive.) Show that it is 89.

**Formal statement A**

```lean
theorem X (x : ZMod 100) (h₀ : x = 9⁻¹) : x = 89
```

**Formal statement B**

```lean
theorem X (x : ℕ) (h₀ : x < 100) (h₁ : x * 9 % 100 = 1) : x = 89
```

## t124

**Informal statement**

Together, Larry and Lenny have $\$$35. Larry has two-fifths of Lenny's amount. How many more dollars than Larry does Lenny have? Show that it is 15.

**Formal statement A**

```lean
theorem X (a b : ℝ) (h₀ : 0 < a ∧ 0 < b) (h₁ : a + b = 35) (h₂ : a = 2 / 5 * b) :
    b - a = 15
```

**Formal statement B**

```lean
theorem X (a b : ℕ) (h₁ : a + b = 35) (h₂ : a = (2:ℚ) / 5 * b) :
  b - a = 15
```

## t138

**Informal statement**

How many natural numbers less than 1000 have exactly three distinct positive integer divisors? Show that it is 11.

**Formal statement A**

```lean
theorem X (S : Finset ℕ)
  (h₀ : ∀ x : ℕ, x ∈ S ↔ 0 < x ∧ x < 1000 ∧ x.divisors.card = 3) : S.card = 11
```

**Formal statement B**

```lean
theorem X (S : Finset ℕ)
  (h₀ : ∀ x : ℕ, x ∈ S ↔ x < 1000 ∧ x.divisors.card = 3) : S.card = 11
```

## t273

**Informal statement**

Suppose $X$ is a nonempty complete metric space, and $\left\{G_{n}\right\}$ is a sequence of dense open sets of $X$. Prove Baire's theorem, namely, that $\bigcap_{1}^{\infty} G_{n}$ is not empty.

**Formal statement A**

```lean
theorem X (X : Type*) [MetricSpace X] [CompleteSpace X] [Nonempty X]
  (G : ℕ → Set X) (hG : ∀ n, IsOpen (G n) ∧ Dense (G n)) :
  ∃ x, ∀ n, x ∈ G n
```

**Formal statement B**

```lean
theorem X (X : Type*) [MetricSpace X] [CompleteSpace X]
  (G : ℕ → Set X) (hG : ∀ n, IsOpen (G n) ∧ Dense (G n)) :
  ∃ x, ∀ n, x ∈ G n
```
