using UnityEngine;

public class EnemyDeath : MonoBehaviour
{
    public GameFlow gameFlow;
    void Start()
    {
        Health health = GetComponent<Health>();
        if (health) health.Died += _ => { if (gameFlow) gameFlow.SendMessage("EnemyDefeated", SendMessageOptions.DontRequireReceiver); };
    }
}
