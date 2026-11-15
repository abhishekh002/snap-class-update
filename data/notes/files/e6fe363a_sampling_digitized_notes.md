# SAMPLING THEOREM (NYQUIST-SHANNON)

## 1. STATEMENT
> "A band-limited continuous-time signal $x(t)$ with $f_{\text{max}}$ (or $W$) can be completely recovered if sampled at $f_s \ge 2f_{\text{max}}$."

---

## VISUAL REPRESENTATION (TIME & FREQUENCY DOMAINS)

### Time Domain
* **Continuous Signal:**
  $$x(t)$$
* **Impulse Train:**
  $$p(t) = \sum_{n=-\infty}^{\infty} \delta(t - nT_s)$$
* **Sampled Signal:**
  $$x_s(t) = x(t) \cdot p(t)$$

### Frequency Domain
* **Band-limited Spectrum:**
  $$X(f) \quad \text{(Band-limited to } f_{\text{max}}\text{)}$$
* **Impulse Train Spectrum:**
  $$P(f) \quad \text{(Impulse Train in } f \text{ with spacing } f_s\text{)}$$
* **Sampled Spectrum (Convolution):**
  $$X_s(f) = X(f) * P(f)$$

---

## KEY TERMS
* **Nyquist Rate ($f_N$):**
  $$f_N = 2f_{\text{max}}$$
* **Nyquist Interval ($T_s$):**
  $$T_s = \frac{1}{2f_{\text{max}}}$$

---

## 2. DERIVATION (Impulse Train Sampling)

* **Time Domain:**
  $$x_s(t) = x(t) \cdot \sum_{n=-\infty}^{\infty} \delta(t - nT_s) = \sum_{n=-\infty}^{\infty} x(t)\delta(t - nT_s)$$

* **Frequency Domain:**
  $$X_s(f) = \frac{1}{T_s} \sum_{n=-\infty}^{\infty} X(f - nf_s)$$

---

## 3. CONDITIONS
* **No Aliasing:** $f_s \ge 2f_{\text{max}}$ (spectra do not overlap)
* **Aliasing:** $f_s < 2f_{\text{max}}$ (spectra overlap, fold-over distortion occurs)

---

## Key Concepts Summary
1. **Band-limiting:** Signals must be strictly limited to a maximum frequency $f_{\text{max}}$ to prevent infinite bandwidth requirements.
2. **Sampling Rate Constraint:** To reconstruct a continuous signal unambiguously from its samples, the sampling frequency $f_s$ must be at least twice the maximum frequency component ($f_s \ge 2f_{\text{max}}$).
3. **Aliasing Prevention:** Sampling below the Nyquist rate causes spectral overlap (aliasing), making perfect signal reconstruction impossible.