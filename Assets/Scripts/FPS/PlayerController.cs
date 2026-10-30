using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class PlayerController : MonoBehaviour
{
    [Header("Movement")]
    public float moveSpeed = 6f;
    public float jumpHeight = 1.2f;
    public float gravity = -20f;
    public Transform groundCheck;
    public float groundDistance = 0.25f;
    public LayerMask groundMask = ~0;

    private CharacterController controller;
    private float verticalVelocity;
    private bool isGrounded;

    void Awake() => controller = GetComponent<CharacterController>();

    void Update()
    {
        isGrounded = groundCheck != null
            ? Physics.CheckSphere(groundCheck.position, groundDistance, groundMask)
            : controller.isGrounded;
        if (isGrounded && verticalVelocity < 0) verticalVelocity = -2f;

        Vector2 input = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
        Vector3 move = (transform.right * input.x + transform.forward * input.y).normalized;
        controller.Move(move * moveSpeed * Time.deltaTime);

        if (Input.GetButtonDown("Jump") && isGrounded)
            verticalVelocity = Mathf.Sqrt(jumpHeight * -2f * gravity);
        verticalVelocity += gravity * Time.deltaTime;
        controller.Move(Vector3.up * verticalVelocity * Time.deltaTime);
    }
}
