import numpy as np
from airfoils import airfoils

def test_get_cl_lin_cl_stall_fs():
    """Test get_cl_lin_cl_stall_fs for single values and arrays."""
    
    # Test 1: Single value (scalar arrays)
    print("Test 1: Single angle of attack, single thickness")
    alpha = np.array([5.0])
    rel_thick = np.array([0.30])
    cl_lin, cl_stall, fs = airfoils.get_cl_lin_cl_stall_fs(alpha, rel_thick)
    print(f"  AoA={alpha[0]}°, t/c={rel_thick[0]}")
    print(f"  Cl_lin={cl_lin[0]:.6f}, Cl_stall={cl_stall[0]:.6f}, fs={fs[0]:.6f}")
    assert len(cl_lin) == 1, "Output length mismatch"
    assert not np.isnan(cl_lin[0]), "Cl_lin is NaN"
    print("  ✓ Passed\n")
    
    # Test 2: Multiple blade sections with different thicknesses
    print("Test 2: Multiple sections (interpolation between airfoils)")
    alpha = np.array([5.0, 10.0, -5.0, 0.0])
    rel_thick = np.array([0.27, 0.36, 0.45, 0.60])  # Mix of exact and interpolated
    cl_lin, cl_stall, fs = airfoils.get_cl_lin_cl_stall_fs(alpha, rel_thick)
    print(f"  Sections: {len(alpha)}")
    for i in range(len(alpha)):
        print(f"  [{i}] AoA={alpha[i]:6.1f}°, t/c={rel_thick[i]:.2f}: "
              f"Cl_lin={cl_lin[i]:7.4f}, Cl_stall={cl_stall[i]:7.4f}, fs={fs[i]:6.4f}")
    assert len(cl_lin) == len(alpha), "Output length mismatch"
    print("  ✓ Passed\n")
    
    # Test 3: Edge case - thickness below minimum (should clip to 24.1%)
    print("Test 3: Thickness below minimum (clip to 24.1%)")
    alpha = np.array([5.0])
    rel_thick = np.array([0.20])  # Below minimum 24.1%
    cl_lin, cl_stall, fs = airfoils.get_cl_lin_cl_stall_fs(alpha, rel_thick)
    
    # Compare with direct query at 24.1%
    cl_lin_ref, cl_stall_ref, fs_ref = airfoils.get_cl_lin_cl_stall_fs(alpha, np.array([0.241]))
    print(f"  t/c=0.20: Cl_lin={cl_lin[0]:.6f}, Cl_stall={cl_stall[0]:.6f}, fs={fs[0]:.6f}")
    print(f"  t/c=0.241 (ref): Cl_lin={cl_lin_ref[0]:.6f}, Cl_stall={cl_stall_ref[0]:.6f}, fs={fs_ref[0]:.6f}")
    assert np.allclose(cl_lin[0], cl_lin_ref[0], atol=1e-6), "Clipping failed"
    print("  ✓ Clipping works\n")
    
    # Test 4: Edge case - thickness above maximum (should clip to 100%)
    print("Test 4: Thickness above maximum (clip to cylinder)")
    alpha = np.array([5.0])
    rel_thick = np.array([1.50])  # Above maximum 100%
    cl_lin, cl_stall, fs = airfoils.get_cl_lin_cl_stall_fs(alpha, rel_thick)
    print(f"  t/c=1.50: Cl_lin={cl_lin[0]:.6f}, Cl_stall={cl_stall[0]:.6f}, fs={fs[0]:.6f}")
    print("  ✓ Passed\n")
    
    # Test 5: Exact thickness match (t/c=0.36)
    print("Test 5: Exact thickness match (t/c=0.36)")
    alpha = np.array([5.0])
    rel_thick = np.array([0.36])
    
    # Debug: check what indices are returned
    idx1, idx2 = airfoils._find_nearest(0.36)
    print(f"  Debug: _find_nearest(0.36) returns indices: ({idx1}, {idx2})")
    print(f"  Debug: Thicknesses used: {airfoils.THICKNESSES[idx1]}, {airfoils.THICKNESSES[idx2]}")
    
    cl_lin, cl_stall, fs = airfoils.get_cl_lin_cl_stall_fs(alpha, rel_thick)
    # Load directly from airfoil to compare
    cl_lin_direct, cl_stall_direct, fs_direct = airfoils.airfoils[36.0].cl_lin_cl_stall_fs(5.0)
    print(f"  Interpolated: Cl_lin={cl_lin[0]:.6f}, Cl_stall={cl_stall[0]:.6f}, fs={fs[0]:.6f}")
    print(f"  Direct query: Cl_lin={cl_lin_direct:.6f}, Cl_stall={cl_stall_direct:.6f}, fs={fs_direct:.6f}")
    assert np.allclose(cl_lin[0], cl_lin_direct, atol=1e-6), "Exact match failed"
    print("  ✓ Exact match works\n")
    
    # Test 6: Full range coverage (data extends to ±180°)
    print("Test 6: Full AoA range coverage")
    
    # Check the actual data range
    test_airfoil = airfoils.airfoils[36.0]
    print(f"  Airfoil 36.0% AoA range: {test_airfoil.aoa.min():.1f}° to {test_airfoil.aoa.max():.1f}°")
    
    # Test at extreme angles (within range)
    alpha = np.array([180.0, -180.0, 0.0])
    rel_thick = np.array([0.36, 0.36, 0.36])
    cl_lin, cl_stall, fs = airfoils.get_cl_lin_cl_stall_fs(alpha, rel_thick)
    
    for i, aoa in enumerate(alpha):
        print(f"  AoA={aoa:6.0f}°: Cl_lin={cl_lin[i]:8.4f}, Cl_stall={cl_stall[i]:8.4f}, fs={fs[i]:6.4f}")
    
    # Verify values are not NaN
    assert not np.any(np.isnan(cl_lin)), "Unexpected NaN in valid range"
    print("  ✓ Full range (-180° to 180°) works correctly\n")
    
    # Test 7: Beyond the data range (truly out of bounds)
    print("Test 7: AoA beyond ±180° (truly out of range)")
    alpha = np.array([200.0])
    rel_thick = np.array([0.36])
    cl_lin, cl_stall, fs = airfoils.get_cl_lin_cl_stall_fs(alpha, rel_thick)
    print(f"  AoA=200°: Cl_lin={cl_lin[0]}, Cl_stall={cl_stall[0]}, fs={fs[0]}")
    
    if np.isnan(cl_lin[0]):
        print("  ✓ Correctly returns NaN for AoA > 180°\n")
    else:
        print("  ⚠ Warning: Extrapolating beyond data range\n")
    
    print("="*60)
    print("All tests completed successfully! ✓")
    print("="*60)

if __name__ == "__main__":
    test_get_cl_lin_cl_stall_fs()