using UnityEngine;
using UnityEngine.UI;

public class FPSHUD : MonoBehaviour
{
    public Health playerHealth;
    public Weapon weapon;
    public Text healthText;
    public Text ammoText;
    public Text messageText;

    void Update()
    {
        if (playerHealth && healthText) healthText.text = $"HP {Mathf.CeilToInt(playerHealth.Current)}";
        if (weapon && ammoText) ammoText.text = weapon.IsReloading ? "RELOADING" : $"AMMO {weapon.AmmoInMagazine}/{weapon.reserveAmmo}";
    }
    public void ShowMessage(string message) { if (messageText) messageText.text = message; }
}
