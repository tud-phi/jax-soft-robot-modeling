# Contributing

Thank you for your interest in contributing to JAX Soft Robot Modelling! This guide will help you get started.

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/jax-soft-robot-modelling.git
cd jax-soft-robot-modelling
```

### 2. Install Development Dependencies

```bash
pip install -e ".[dev,docs,examples]"
```

### 3. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 4. Environment Variables

```bash
source 01-configure-env-vars.sh
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow our coding standards:
- Use type hints
- Write docstrings in Google format
- Follow PEP 8 style guidelines
- Add tests for new functionality

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_planar_pcs_num.py

# Run with coverage
pytest --cov=jsrm
```

### 4. Format Code

```bash
# Auto-format with ruff
ruff format .

# Check for issues
ruff check .
```

### 5. Build Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add new robot system"
```

Use conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions
- `refactor:` for code refactoring

## Adding New Robot Systems

### 1. System Structure

Create a new module in `src/jsrm/systems/`:

```
src/jsrm/systems/your_robot/
├── __init__.py
├── symbolic_derivation.py
├── numerical_implementation.py
└── factory.py
```

### 2. Factory Pattern

Follow the established factory pattern:

```python
def factory(parameters):
    """
    Factory function for your robot system.
    
    Args:
        parameters: System-specific parameters
        
    Returns:
        tuple: (ode_fn, forward_kinematics, jacobian_fn, additional_fns)
    """
    pass
```

### 3. Testing

Add comprehensive tests in `tests/`:

```python
def test_your_robot_forward_kinematics():
    """Test forward kinematics computation."""
    pass

def test_your_robot_dynamics():
    """Test dynamic simulation."""
    pass
```

### 4. Documentation

Add examples and documentation:
- Example script in `examples/`
- Documentation in `docs/`
- Docstrings for all functions

## Code Style

### Python Style

- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 88 characters
- Use descriptive variable names

### Docstring Format

Use Google-style docstrings:

```python
def forward_kinematics(params: Dict, q: Array) -> Array:
    """
    Compute forward kinematics for the robot.
    
    Args:
        params: Dictionary of robot parameters including:
            - l: Segment lengths
            - r: Segment radii  
            - E: Young's moduli
        q: Configuration vector of shape (n_dof,)
        
    Returns:
        End-effector position of shape (2,) for planar robots
        
    Raises:
        ValueError: If configuration vector has wrong dimensions
        
    Example:
        >>> params = {"l": jnp.array([0.1]), "r": jnp.array([0.01])}
        >>> q = jnp.array([0.0, 0.0, -1.0])
        >>> pos = forward_kinematics(params, q)
    """
```

### JAX Best Practices

- Use `jax.numpy` instead of `numpy`
- Make functions JAX-transformable (pure, no side effects)
- Use `jit` for performance-critical functions
- Avoid Python loops in favor of JAX operations

## Testing Guidelines

### Test Structure

```python
import pytest
import jax.numpy as jnp
from jsrm.systems import your_system

class TestYourSystem:
    def setup_method(self):
        """Set up test fixtures."""
        self.params = {
            # Test parameters
        }
    
    def test_forward_kinematics(self):
        """Test forward kinematics."""
        # Test implementation
        pass
    
    def test_jacobian_computation(self):
        """Test Jacobian computation."""
        # Test implementation
        pass
```

### Test Coverage

Aim for high test coverage:
- Unit tests for individual functions
- Integration tests for complete workflows
- Property-based tests for mathematical relationships
- Regression tests for bug fixes

## Documentation Guidelines

### API Documentation

- Document all public functions and classes
- Include examples in docstrings
- Use type hints consistently
- Explain mathematical concepts clearly

### User Documentation

- Write clear, step-by-step tutorials
- Include complete, runnable examples
- Explain the mathematical background
- Provide troubleshooting guides

## Submitting Changes

### 1. Push Changes

```bash
git push origin feature/your-feature-name
```

### 2. Create Pull Request

- Provide a clear description of changes
- Reference related issues
- Include screenshots for UI changes
- Ensure all tests pass

### 3. Code Review

- Address reviewer feedback
- Update tests and documentation as needed
- Maintain a clean commit history

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions in pull requests
- Check existing documentation and examples
- Ask questions in the community

Thank you for contributing to JSRM!
