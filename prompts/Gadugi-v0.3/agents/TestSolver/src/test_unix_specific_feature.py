   @pytest.mark.skipif(sys.platform == "win32",
                      reason="Unix-specific functionality")
   def test_unix_specific_feature():
       """Test that only works on Unix-like systems."""
       pass
   