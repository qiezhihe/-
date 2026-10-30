using UnityEngine;
using UnityEngine.SceneManagement;

public class GameFlow : MonoBehaviour
{
    public Health playerHealth;
    public string nextSceneName;
    public float restartDelay = 1.5f;
    public int enemiesRemaining;
    private bool ended;

    void OnEnable() { if (playerHealth) playerHealth.Died += OnPlayerDied; }
    void OnDisable() { if (playerHealth) playerHealth.Died -= OnPlayerDied; }
    void OnPlayerDied(Health _) { if (!ended) { ended = true; Invoke(nameof(Restart), restartDelay); } }
    void Restart() => SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    public void EnemyDefeated()
    {
        if (ended) return;
        enemiesRemaining = Mathf.Max(0, enemiesRemaining - 1);
        if (enemiesRemaining == 0) CompleteLevel();
    }
    public void CompleteLevel()
    {
        if (ended) return; ended = true;
        if (!string.IsNullOrEmpty(nextSceneName)) SceneManager.LoadScene(nextSceneName);
    }
}
