using System;
using UnityEngine;

public class Health : MonoBehaviour
{
    public float maxHealth = 100f;
    public bool destroyOnDeath = true;
    public event Action<Health> Died;
    public float Current { get; private set; }

    void Awake() => Current = maxHealth;
    public void TakeDamage(float amount)
    {
        if (Current <= 0) return;
        Current = Mathf.Max(0, Current - Mathf.Max(0, amount));
        if (Current == 0) Die();
    }
    void Die()
    {
        Died?.Invoke(this);
        if (destroyOnDeath) Destroy(gameObject);
    }
}
