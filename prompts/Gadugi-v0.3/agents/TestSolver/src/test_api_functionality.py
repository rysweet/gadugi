   @pytest.mark.skipif(not os.getenv('API_KEY'),
                      reason="API key required but not available")
   def test_api_functionality():
       """Test that requires external API access."""
       pass
   