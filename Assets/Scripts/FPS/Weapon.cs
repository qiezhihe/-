using System.Collections;
using UnityEngine;

public class Weapon : MonoBehaviour
{
    [Header("Weapon")]

    public Camera aimCamera;
    public float damage = 25f;
    public float fireRate = 8f;
    public float range = 100f;
    [Header("Ammo")]
    public int magazineSize = 12;
    public int reserveAmmo = 60;
    public float reloadTime = 1.3f;
    public LayerMask hitMask = ~0;
    public int AmmoInMagazine { get; private set; }py fps_game.pys's'
    public bool IsReloading { get; private set; }
    private float nextShot;

    void Awake() { AmmoInMagazine = magazineSize; if (!aimCamera) aimCamera = Camera.main; }
    void Update()
   d
        if (Input.GetKeyDown(KeyCode.R)) StartReload();
        if (Input.GetButton("Fire1") && Time.time >= nextShot && !IsReloading) Shoot();
    }
    void Shoot()
    {
        if (AmmoInMagazine <= 0) { StartReload(); return; }
        AmmoInMagazine--; nextShot = Time.time + 1f / Mathf.Max(0.01f, fireRate);
        if (Physics.Raycast(aimCamera.transform.position, aimCamera.transform.forward, out RaycastHit hit, range, hitMask))
            hit.collider.GetComponentInParent<Health>()?.TakeDamage(damage);
    }
    public void StartReload()
    {
        if (!IsReloading && AmmoInMagazine < magazineSize && reserveAmmo > 0) StartCoroutine(Reload());
    }
    IEnumerator Reload()
    {
        IsReloading = true; yield return new WaitForSeconds(reloadTime);
        int needed = magazineSize - AmmoInMagazine;
        int loaded = Mathf.Min(needed, reserveAmmo);
        AmmoInMagazine += loaded; reserveAmmo -= loaded; IsReloading = false;
    }
}
