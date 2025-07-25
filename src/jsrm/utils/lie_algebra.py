import jax.numpy as jnp
from jax import lax

# for documentation
from jax import Array
from typing import Sequence, Optional, Tuple

# ================================================================================================
# SE(2) operators
# ===================================
J = jnp.array([[0, -1], [1, 0]])

def hat_SE2(
    vec3:Array
)-> Array:
    """
    Computes the hat operator for a 3D vector of se(2).

    Args:
        vec3 (Array): array-like, shape (3,1)
            A 3-dimensional vector representing the screw. 
            The first element correspond to the angular component, 
            and the last two elements correspond to the linear components.

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the hat operator of the input screw vector.
    """
    vec3 = vec3.reshape(-1)  # Ensure vec3 is a 1D array
    
    ang = vec3[0] # Angular part
    lin = vec3[1:].reshape((2, 1))  # Linear as a (2,1) vector
    
    angtilde = ang * J
    
    hat = jnp.block([
        [angtilde, lin],
        [jnp.zeros((1, 2)), jnp.zeros((1, 1))] 
    ])
    
    return hat

def exp_SE2(
    vec3: Array
    ) -> Array:
    """
    Computes the exponential map for a 3D vector of se(2).
    
    Args:
        vec3 (Array): array-like, shape (3,1)
            A 3-dimensional vector representing the position.
            [theta, x, y] where theta is the rotation angle and (x, y) is the translation vector.
    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the exponential map of the input screw vector.
    """
    vec3 = vec3.reshape(-1)  # Ensure vec3 is a 1D array
    
    theta = vec3[0]
    p = vec3[1:].reshape((2, 1))
    
    cos = jnp.cos(theta)
    sin = jnp.sin(theta)
    R = jnp.array([[cos, -sin], [sin, cos]])  # Rotation matrix
    
    g = jnp.block([
        [R, p],
        [jnp.zeros((1, 2)), jnp.ones((1, 1))] 
    ])
    
    return g

def adjoint_se2(
    vec3: Array
    ) -> Array:
    """
    Computes the adjoint representation of a vector of se(2).

    Args:
        vec3 (Array): array-like, shape (3, 1)
            A 3-dimensional vector representing the screw.
            The first element correspond to the angular component,
            and the last two elements correspond to the linear component.

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the adjoint transformation of the input screw vector.
    """
    vec3 = vec3.reshape(-1)  # Ensure vec6 is a 1D array

    ang = vec3[0]
    lin = vec3[1:].reshape((2, 1))  # Linear as a (3,1) vector

    adj = jnp.concatenate(
        [jnp.zeros((1, 3)), jnp.concatenate([-J @ lin, ang * J], axis=1)]
    )

    return adj

def coadjoint_se2(
    vec3: Array
    ) -> Array:
    """
    Computes the co-adjoint representation of a vector of se(2).

    Args:
        vec3 (Array): array-like, shape (3, 1)
            A 3-dimensional vector representing the screw.
            The first element correspond to the angular component,
            and the last two elements correspond to the linear component.

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the co-adjoint transformation of the input screw vector.
    """
    vec3 = vec3.reshape(-1)  # Ensure vec6 is a 1D array

    ang = vec3[0]
    lin = vec3[1:].reshape((2, 1))  # Linear as a (3,1) vector

    adj_star = jnp.concatenate(
        [jnp.zeros((3, 1)), jnp.concatenate([lin.T @ J, ang * J], axis=0)], axis=1
    )

    return adj_star


def Adjoint_g_SE2(
    mat3: Array
    ) -> Array:
    """
    Computes the adjoint representation of a 3x3 matrix.

    Args:
        mat4 (Array): array-like, shape (4,4)
            A 4x4 matrix representing the transformation.

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the Adjoint transformation of the input matrix.
    """
    R = mat3[:2, :2]  # Extract the angular part (top-left 2x2 block)
    t = mat3[:2, 2].reshape((2, 1))  # Extract the linear part (top-right column)

    Adjoint = jnp.concatenate(
        [
            jnp.concatenate([jnp.ones(((1, 1))), jnp.zeros((1, 2))], axis=1),
            jnp.concatenate([-J @ t, R], axis=1),
        ]
    )

    return Adjoint

def Adjoint_g_inv_SE2(
    mat3: Array
    ) -> Array:
    """
    Computes the adjoint representation of a 3x3 matrix.

    Args:
        mat4 (Array): array-like, shape (4,4)
            A 4x4 matrix representing the transformation.

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the Adjoint transformation of the input matrix.
    """
    Adj = Adjoint_g_SE2(mat3)  # Adjoint representation of the input matrix
    
    # Extract R and -Jt from the Adjoint matrix
    R = Adj[1:, 1:]
    mJt = Adj[1:, 0].reshape(-1, 1)

    # Compute the inverse using the Schur complement
    R_inv = jnp.transpose(R)  # Since R is a rotation matrix, R^-1=R^T
    # Construct the inverse Adjoint matrix
    inverse_Adjoint = jnp.concatenate(
        [
            jnp.concatenate([jnp.ones(((1, 1))), jnp.zeros((1, 2))], axis=1),
            jnp.concatenate([-R_inv @ mJt, R_inv], axis=1),
        ]
    )

    return inverse_Adjoint

def Adjoint_gi_se2(
    xi_i: Array,
    s_i : float,
    eps: float,
) -> Array:
    """
    Computes the adjoint representation of a position of a points at s_i (local curvilinear coordinate)
    along a rod in SE(2) deformed ine the current segment according to a strain vector xi_i.

    Args:
        xi_i (Array): array-like, shape (3,1)
            A 3-dimensional vector representing the screw in the current segment.
        s_i (float):
            The curvilinear coordinate along the rod, representing the position of a point in the current segment.
        eps (float): small value to avoid division by zero

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the adjoint transformation of the input screw vector at the specified position.
    """
    # We suppose here that theta is not zero thanks to a previous use of apply_eps
    theta = xi_i[0]  # Angular part
    adjoint_xi_i = adjoint_se2(xi_i)  # Adjoint representation of the input vector

    cos = jnp.cos(s_i * theta)
    sin = jnp.sin(s_i * theta)

    Adjoint = lax.cond(
        jnp.abs(theta) <= eps,
        lambda _: jnp.eye(3) + s_i * adjoint_xi_i,  # Avoid division by zero
        lambda _: (
            jnp.eye(3)
            + 1 / (2 * theta) * (3 * sin - s_i * theta * cos) * adjoint_xi_i
            + 1
            / (2 * jnp.power(theta, 2))
            * (4 - 4 * cos - s_i * theta * sin)
            * jnp.linalg.matrix_power(adjoint_xi_i, 2)
            + 1
            / (2 * jnp.power(theta, 3))
            * (sin - s_i * theta * cos)
            * jnp.linalg.matrix_power(adjoint_xi_i, 3)
            + 1
            / (2 * jnp.power(theta, 4))
            * (2 - 2 * cos - s_i * theta * sin)
            * jnp.linalg.matrix_power(adjoint_xi_i, 4)
        ),
        operand=None
    )

    return Adjoint

def Adjoint_gi_se2_inv(
    xi_i: Array,
    s_i : float,
    eps : float,
) -> Array:
    """
    Computes the adjoint representation of a position of a points at s_i (local curvilinear coordinate)
    along a rod in SE(2) deformed ine the current segment according to a strain vector xi_i.

    Args:
        xi_i (Array): array-like, shape (3,1)
            A 3-dimensional vector representing the screw in SE(2).
        s_i (float):
            The curvilinear coordinate along the rod, representing the position of a point in the n-th segment.
        eps (float): small value to avoid division by zero

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the adjoint transformation of the input screw vector at the specified position.
    """
    Adj = Adjoint_gi_se2(xi_i, s_i, eps=eps)  # Adjoint representation of the input vector

    # Extract R and -Jt from the Adjoint matrix
    R = Adj[1:, 1:]
    mJt = Adj[1:, 0].reshape(-1, 1)

    # Compute the inverse using the Schur complement
    R_inv = jnp.transpose(R)  # Since R is a rotation matrix, R^-1=R^T
    # Construct the inverse Adjoint matrix
    inverse_Adjoint = jnp.concatenate(
        [
            jnp.concatenate([jnp.ones(((1, 1))), jnp.zeros((1, 2))], axis=1),
            jnp.concatenate([-R_inv @ mJt, R_inv], axis=1),
        ]
    )

    return inverse_Adjoint

def Tangent_gi_se2(
    xi_i: Array,
    s_i: float,
    eps: float,
) -> Array:
    """
    Computes the tangent representation of a position of a points at s_i (local curvilinear coordinate)
    along a rod in SE(2) deformed in the current segment according to a strain vector xi_i.

    Args:
        xi_i (Array): array-like, shape (3,1)
            A 3-dimensional vector representing the screw in SE(2).
        s_i (float):
            The curvilinear coordinate along the rod, representing the position of a point in the n-th segment.
        eps (float): small value to avoid division by zero

    Returns:
        Array: shape (3, 3)
            A 3x3 matrix representing the tangent transformation of the input screw vector at the specified position.
    """
    # We suppose here that theta is not zero thanks to a previous use of apply_eps
    theta = xi_i[0]  # Angular part
    adjoint_xi_i = adjoint_se2(xi_i)  # Adjoint representation of the input vector

    cos = jnp.cos(s_i * theta)
    sin = jnp.sin(s_i * theta)

    Tangent = lax.cond(
        jnp.abs(theta) <= eps,
        lambda _: s_i * jnp.eye(3) + s_i**2/2 * adjoint_xi_i,
        lambda _: (
            s_i * jnp.eye(3)
            + 1 / (2 * jnp.power(theta, 2)) * (4 - 4 * cos - s_i * theta * sin) * adjoint_xi_i
            + 1
            / (2 * jnp.power(theta, 3))
            * (4 * s_i * theta - 5 * sin + s_i * theta * cos)
            * jnp.linalg.matrix_power(adjoint_xi_i, 2)
            + 1
            / (2 * jnp.power(theta, 4))
            * (2 - 2 * cos - s_i * theta * sin)
            * jnp.linalg.matrix_power(adjoint_xi_i, 3)
            + 1
            / (2 * jnp.power(theta, 5))
            * (2 * s_i * theta - 3 * sin + s_i * theta * cos)
            * jnp.linalg.matrix_power(adjoint_xi_i, 4)
        ),
        operand=None
    )

    return Tangent

# ================================================================================================
# Shared operators
# ============================
def compute_weighted_sums(M: Array, vecm: Array, idx: int) -> Array:
    """
    Compute the weighted sums of the matrix product of M and vecm,

    Args:
        M (Array): array of shape (N, m, m)
           Describes the matrix to be multiplied with vecm
        vecm (Array): array-like of shape (N, m)
           Describes the vector to be multiplied with M
        idx (int): index of the last row to be summed over

    Returns:
        Array: array of shape (N, m)
           The result of the weighted sums. For each i, the result is the sum of the products of M[i, j] and vecm[j] for j from 0 to idx.
    """
    N = M.shape[0]
    # Matrix product for each j: (N, m, m) @ (N, m, 1) -> (N, m)
    prod = jnp.einsum("nij,nj->ni", M, vecm)

    # Triangular mask for partial sum: (N, N)
    # mask[i, j] = 1 if j >= i and j <= idx
    mask = (jnp.arange(N)[:, None] <= jnp.arange(N)[None, :]) & (
        jnp.arange(N)[None, :] <= idx
    )
    mask = mask.astype(M.dtype)  # (N, N)

    # Extend 6-dimensional mask (N, N, 1) to apply to (N, m)
    masked_prod = mask[:, :, None] * prod[None, :, :]  # (N, N, m)

    # Sum over j for each i : (N, m)
    result = masked_prod.sum(axis=1)  # (N, m)
    return result
