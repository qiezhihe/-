using UnityEngine;

public class FirstPersonCamera : MonoBehaviour
{
    public Transform playerBody;
    public float sensitivity = 2.5f;
    public float maxLookAngle = 89f;
    private float pitch;

    void Start() { Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false; }

    void Update()
    {
        float yaw = Input.GetAxis("Mouse X") * sensitivity;
        pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * sensitivity, -maxLookAngle, maxLookAngle);
        transform.localRotation = Quaternion.Euler(pitch, 0, 0);
        if (playerBody) playerBody.Rotate(Vector3.up * yaw);
    }
}
