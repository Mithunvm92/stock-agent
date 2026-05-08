from agents.hybrid_analyzer import HybridAnalyzer
from utils.helpers import print_header
import traceback

def main():
    try:
        print_header("Hybrid ML + LLM Stock Analyzer")
        print("🚀 Starting Agent...\n")
        
        analyzer = HybridAnalyzer()
        
        while True:
            print("\n" + "-"*70)
            user_input = input("Enter Symbol [RELIANCE.NS] or 'quit': ").strip().upper()
            
            if user_input in ['QUIT', 'Q', 'EXIT']:
                print("👋 Goodbye!")
                break
                
            symbol = user_input if user_input else "RELIANCE.NS"
            
            # Sample ML Signal (Replace with your actual ML output later)
            ml_signal = {
                'symbol': symbol,
                'signal_type': 'ENTRY_LONG',
                'confidence': 0.55,
                'latest_probability': 0.3926,
                'rr_ratio': 2.0,
                'entry_price': 1435.2,
                'stop_loss': 1398.31,
                'take_profit': 1508.99,
                'explanation': 'Bullish structure with RSI 59.0...',
                'regime': 'bull'
            }
            
            print(f"\n🔍 Analyzing {symbol}...")
            analyzer.run_full_analysis(symbol, ml_signal)
            
    except Exception as e:
        print("\n❌ ERROR OCCURRED:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
