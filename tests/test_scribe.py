"""
🖋️ SCRIBE CALIBRATION TEST
Quick validation of Scribe's human vs AI detection capabilities
on your 32GB RAM + 1660 Ti setup.

Usage:
  1. Insert your own writing sample in sample_human
  2. Insert an AI-generated sample in sample_ai
  3. Run: python test_scribe.py
  4. Review the AI Detection Report
"""

import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEGACY_DIR = PROJECT_ROOT / "legacy"
if str(LEGACY_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_DIR))


from src.scribe.engine import ScribeEngine

# ============================================================================
# SAMPLE TEXTS - Replace with your own for accurate calibration
# ============================================================================

# YOUR WRITING (Replace with a paragraph of your own text)
sample_human = """
The intersection of cognitive science and digital communication reveals 
a fascinating paradox: while technology enables unprecedented information 
dissemination, it simultaneously fragments our collective attention. I've 
always found it curious how algorithmic curation shapes what we consider 
important. The challenge isn't just technological—it's profoundly human.
"""

# AI-GENERATED TEXT (Replace with ChatGPT/Claude output)
sample_ai = """
The intersection of cognitive science and digital communication represents 
a significant area of contemporary research. Digital technologies have 
facilitated information distribution on a scale previously unimaginable. 
Additionally, algorithmic systems play a substantial role in content 
curation. This phenomenon raises important considerations regarding attention 
mechanisms and information processing in modern societies.
"""

# ============================================================================
# CALIBRATION TEST
# ============================================================================

print("\n" + "="*80)
print("🖋️  SCRIBE CALIBRATION TEST - Human vs AI Detection")
print("="*80)

try:
    scribe = ScribeEngine()
    print("\n✅ ScribeEngine initialized")

    # ====================================================================
    # PHASE 1: Extract Fingerprints
    # ====================================================================
    print("\n" + "─"*80)
    print("PHASE 1: Extracting Linguistic Fingerprints")
    print("─"*80)

    fp_human = scribe.extract_linguistic_fingerprint(sample_human, author_id="test_human")
    fp_ai = scribe.extract_linguistic_fingerprint(sample_ai, author_id="test_ai")

    print("\n📊 HUMAN WRITING FINGERPRINT:")
    print(f"  • Avg sentence length: {fp_human.avg_sentence_length:.1f} words")
    print(f"  • Sentence variance (std): {fp_human.sentence_length_std:.2f}")
    print(f"  • Lexical diversity: {fp_human.lexical_diversity:.3f} (0-1 scale)")
    print(f"  • Type-token ratio: {fp_human.type_token_ratio:.3f}")
    print(f"  • Passive voice: {fp_human.passive_voice_ratio:.1%}")
    print(f"  • Active voice: {fp_human.active_voice_ratio:.1%}")
    print(f"  • Punctuation variety: {len(fp_human.punctuation_profile)} types")
    print(f"  • Signal dimensions: {len(fp_human.signal_vector)}")
    print(f"  • Words analyzed: {fp_human.text_sample_count}")

    print("\n📊 AI-GENERATED FINGERPRINT:")
    print(f"  • Avg sentence length: {fp_ai.avg_sentence_length:.1f} words")
    print(f"  • Sentence variance (std): {fp_ai.sentence_length_std:.2f}")
    print(f"  • Lexical diversity: {fp_ai.lexical_diversity:.3f} (0-1 scale)")
    print(f"  • Type-token ratio: {fp_ai.type_token_ratio:.3f}")
    print(f"  • Passive voice: {fp_ai.passive_voice_ratio:.1%}")
    print(f"  • Active voice: {fp_ai.active_voice_ratio:.1%}")
    print(f"  • Punctuation variety: {len(fp_ai.punctuation_profile)} types")
    print(f"  • Signal dimensions: {len(fp_ai.signal_vector)}")
    print(f"  • Words analyzed: {fp_ai.text_sample_count}")

    # ====================================================================
    # PHASE 2: Comparative Analysis
    # ====================================================================
    print("\n" + "─"*80)
    print("PHASE 2: Comparative Analysis (Human vs AI)")
    print("─"*80)

    # Voice ratio comparison (AI indicator)
    voice_diff = abs(fp_human.passive_voice_ratio - fp_ai.passive_voice_ratio)
    print("\n🔄 VOICE RATIO COMPARISON:")
    print(f"  • Human passive voice: {fp_human.passive_voice_ratio:.1%}")
    print(f"  • AI passive voice: {fp_ai.passive_voice_ratio:.1%}")
    print(f"  • Difference: {voice_diff:.1%}")
    if voice_diff < 0.10:
        print("    ⚠️  WARNING: Voices similar (AI mimicking?)")
    elif voice_diff > 0.20:
        print("    ✅ CLEAR DISTINCTION: Different voice patterns")
    else:
        print("    ⚡ MODERATE DIFFERENCE: Noticeable variance")

    # Sentence length variance
    length_diff = abs(fp_human.sentence_length_std - fp_ai.sentence_length_std)
    print("\n📏 SENTENCE STRUCTURE:")
    print(f"  • Human sentence variance: {fp_human.sentence_length_std:.2f}")
    print(f"  • AI sentence variance: {fp_ai.sentence_length_std:.2f}")
    print(f"  • Difference: {length_diff:.2f}")
    if fp_human.sentence_length_std > fp_ai.sentence_length_std:
        print("    ✅ HUMAN: More varied sentence lengths (natural)")
        print("    ℹ️  AI: More uniform (controlled)")
    else:
        print("    ⚠️  Both show similar variance")

    # Lexical diversity
    diversity_diff = abs(fp_human.lexical_diversity - fp_ai.lexical_diversity)
    print("\n📚 VOCABULARY RICHNESS:")
    print(f"  • Human lexical diversity: {fp_human.lexical_diversity:.3f}")
    print(f"  • AI lexical diversity: {fp_ai.lexical_diversity:.3f}")
    print(f"  • Difference: {diversity_diff:.3f}")
    if fp_human.lexical_diversity > fp_ai.lexical_diversity:
        print("    ✅ HUMAN: Richer vocabulary (more unique words)")
        print("    ℹ️  AI: More formal/repetitive")
    else:
        print("    ✅ AI: Equally or more diverse (well-trained)")

    # Signal vector similarity
    signal_sim = scribe._calculate_signal_similarity(
        fp_human.signal_vector,
        fp_ai.signal_vector
    )
    print("\n🎯 SIGNAL VECTOR SIMILARITY:")
    print(f"  • Cosine similarity: {signal_sim:.3f} (0=different, 1=identical)")
    if signal_sim > 0.85:
        print("    ⚠️  VERY SIMILAR: Hard to distinguish")
    elif signal_sim > 0.70:
        print("    ⚡ MODERATELY SIMILAR: Some overlap in patterns")
    else:
        print("    ✅ DISTINCT: Clear rhetorical differences")

    # ====================================================================
    # PHASE 3: Save Profiles for Later Anomaly Detection
    # ====================================================================
    print("\n" + "─"*80)
    print("PHASE 3: Saving Baseline Profiles")
    print("─"*80)

    scribe.save_author_profile(fp_human, "Test Author (Human)")
    print("✅ Human baseline profile saved")

    # ====================================================================
    # PHASE 4: Anomaly Detection (Does AI sound like human?)
    # ====================================================================
    print("\n" + "─"*80)
    print("PHASE 4: Anomaly Detection (AI-Generated Text Analysis)")
    print("─"*80)
    print("Question: If we pretend the AI text is from our 'human' author,")
    print("          would Scribe detect an anomaly?")

    report = scribe.identify_stylistic_anomalies("test_human", sample_ai)

    if report:
        print(f"\n🚨 ANOMALIES DETECTED ({report.severity} severity, {report.confidence:.1f}% confidence):")
        for anomaly in report.anomalies_detected:
            print(f"\n  {anomaly}")

        print("\n  Baseline metrics:")
        print(f"    • Avg sentence: {report.baseline_profile['avg_sentence_length']:.1f} words")
        print(f"    • Type-token ratio: {report.baseline_profile['type_token_ratio']:.3f}")
        print(f"    • Passive voice: {report.baseline_profile['passive_voice_ratio']:.1%}")

        print("\n  Current metrics (AI text):")
        print(f"    • Avg sentence: {report.current_profile['avg_sentence_length']:.1f} words")
        print(f"    • Type-token ratio: {report.current_profile['type_token_ratio']:.3f}")
        print(f"    • Passive voice: {report.current_profile['passive_voice_ratio']:.1%}")

        if report.severity == "Critical":
            print("\n  ✅ SCRIBE VERDICT: HIGHLY LIKELY AI-GENERATED or GHOSTWRITTEN")
        elif report.severity == "High":
            print("\n  ⚠️  SCRIBE VERDICT: SIGNIFICANT STYLE CHANGE (suspicious)")
        else:
            print("\n  ℹ️  SCRIBE VERDICT: Minor style variation (probably natural)")
    else:
        print("\n✅ No anomalies detected - AI text mimics human style very well")
        print("   (This would be concerning for authentication purposes)")

    # ====================================================================
    # PHASE 5: Attribution Test
    # ====================================================================
    print("\n" + "─"*80)
    print("PHASE 5: Can Scribe Distinguish Them?")
    print("─"*80)
    print("Testing: If Scribe sees new text, can it identify if it's human or AI?")

    # Compare AI text against both profiles
    print("\n🔍 Comparing AI text to known profiles:")
    ai_fp = scribe.extract_linguistic_fingerprint(sample_ai)
    matches = scribe.compare_to_profiles(ai_fp, min_confidence=30)  # Lower threshold

    if matches:
        for i, match in enumerate(matches[:3], 1):
            print(f"  {i}. {match.author_name}: {match.confidence_score:.1f}% "
                  f"({match.match_strength})")
    else:
        print("  No matches found (text is distinctive)")

    # ====================================================================
    # PHASE 6: System Statistics
    # ====================================================================
    print("\n" + "─"*80)
    print("PHASE 6: System Statistics")
    print("─"*80)

    stats = scribe.get_scribe_stats()
    print("\n📊 Database Status:")
    print(f"  • Author profiles stored: {stats['total_author_profiles']}")
    print(f"  • Attribution records: {stats['total_attributions']}")
    print(f"  • Anomaly reports: {stats['total_anomaly_reports']}")
    print(f"  • Database location: {stats['database_path']}")
    print(f"  • Status: {stats['status']}")

    # ====================================================================
    # SUMMARY & RECOMMENDATIONS
    # ====================================================================
    print("\n" + "="*80)
    print("📋 CALIBRATION SUMMARY")
    print("="*80)

    print("\n✅ System Status: OPERATIONAL")
    print("   • Vector extraction: Working")
    print("   • Profile comparison: Working")
    print("   • Anomaly detection: Working")
    print("   • Database: Ready")

    print("\n🎯 Key Findings:")
    print(f"   • Human/AI distinction clarity: {signal_sim:.0%} (0%=clear, 100%=indistinguishable)")
    print(f"   • Voice ratio difference: {voice_diff:.1%}")
    print(f"   • Anomaly detection: {'✅ Active' if report else '⚠️  Needs calibration'}")

    print("\n💡 Recommendations:")
    if signal_sim > 0.85:
        print("   ⚠️  AI text is similar to human - increase profile size")
        print("   → Collect more diverse human writing samples for training")
    else:
        print("   ✅ Good separation - Scribe can distinguish them")

    if voice_diff < 0.10:
        print("   ⚠️  Voice ratios are similar - both texts might be neutral")
        print("   → Use more opinionated writing samples for better calibration")
    else:
        print("   ✅ Voice patterns are distinct - good signal")

    print("\n🚀 Next Steps:")
    print("   1. Replace sample_human with your own 500+ word writing sample")
    print("   2. Replace sample_ai with actual AI-generated content")
    print("   3. Run again and refine anomaly thresholds if needed")
    print("   4. Build 5-10 author profiles for your domain")
    print("   5. Begin real-world testing on your data")

    print("\n" + "="*80)
    print("✅ CALIBRATION TEST COMPLETE")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n❌ Error during calibration: {e!s}")
    import traceback
    traceback.print_exc()
