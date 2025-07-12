#!/usr/bin/env python3
"""
GPU OCR Speed Test - Compare CPU vs GPU OCR performance
"""

import time
import torch
from pathlib import Path
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import tempfile

def test_gpu_availability():
    """Test if CUDA GPU is available"""
    print("🔍 GPU AVAILABILITY CHECK")
    print("=" * 40)
    
    # Check CUDA
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    
    if cuda_available:
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        print(f"GPU Count: {gpu_count}")
        print(f"GPU Name: {gpu_name}")
        print(f"GPU Memory: {gpu_memory:.1f} GB")
        
        return True
    else:
        print("❌ CUDA not available")
        return False

def test_easyocr_speed(pdf_path):
    """Test EasyOCR speed with GPU"""
    try:
        import easyocr
        
        print("\n🚀 TESTING EASYOCR (GPU)")
        print("=" * 40)
        
        # Initialize EasyOCR with GPU
        reader = easyocr.Reader(['en'], gpu=True)
        
        # Convert first page to image
        with tempfile.TemporaryDirectory() as temp_dir:
            pages = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
            
            if pages:
                start_time = time.time()
                
                # Perform OCR
                results = reader.readtext(pages[0])
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Extract text
                extracted_text = ' '.join([result[1] for result in results])
                
                print(f"⏱️ Processing time: {processing_time:.2f} seconds")
                print(f"📄 Text extracted: {len(extracted_text)} characters")
                print(f"📝 Sample: {extracted_text[:200]}...")
                
                return processing_time, len(extracted_text)
                
    except ImportError:
        print("❌ EasyOCR not installed. Install with: pip install easyocr")
        return None, None
    except Exception as e:
        print(f"❌ EasyOCR test failed: {e}")
        return None, None

def test_tesseract_speed(pdf_path):
    """Test current Tesseract speed for comparison"""
    try:
        import pytesseract
        
        print("\n🐌 TESTING TESSERACT (CPU)")
        print("=" * 40)
        
        # Convert first page to image
        with tempfile.TemporaryDirectory() as temp_dir:
            pages = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
            
            if pages:
                start_time = time.time()
                
                # Perform OCR
                extracted_text = pytesseract.image_to_string(pages[0])
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                print(f"⏱️ Processing time: {processing_time:.2f} seconds")
                print(f"📄 Text extracted: {len(extracted_text)} characters")
                print(f"📝 Sample: {extracted_text[:200]}...")
                
                return processing_time, len(extracted_text)
                
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")
        return None, None

def test_paddleocr_speed(pdf_path):
    """Test PaddleOCR speed with GPU"""
    try:
        from paddleocr import PaddleOCR
        
        print("\n⚡ TESTING PADDLEOCR (GPU)")
        print("=" * 40)
        
        # Initialize PaddleOCR with GPU
        ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)
        
        # Convert first page to image
        with tempfile.TemporaryDirectory() as temp_dir:
            pages = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
            
            if pages:
                # Save image temporarily
                img_path = f"{temp_dir}/test_page.png"
                pages[0].save(img_path)
                
                start_time = time.time()
                
                # Perform OCR
                results = ocr.ocr(img_path, cls=True)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Extract text
                extracted_text = ''
                if results and results[0]:
                    extracted_text = ' '.join([line[1][0] for line in results[0]])
                
                print(f"⏱️ Processing time: {processing_time:.2f} seconds")
                print(f"📄 Text extracted: {len(extracted_text)} characters")
                print(f"📝 Sample: {extracted_text[:200]}...")
                
                return processing_time, len(extracted_text)
                
    except ImportError:
        print("❌ PaddleOCR not installed. Install with: pip install paddlepaddle-gpu paddleocr")
        return None, None
    except Exception as e:
        print(f"❌ PaddleOCR test failed: {e}")
        return None, None

def main():
    """Main speed test function"""
    print("🚀 GPU OCR SPEED TEST FOR RTX 4070")
    print("=" * 50)
    
    # Test GPU availability
    gpu_available = test_gpu_availability()
    
    if not gpu_available:
        print("\n❌ No GPU acceleration available")
        return
    
    # Find a test PDF
    pdf_dir = Path("/home/herb/Desktop/Not Backed Up/Anderson's Library/Andy/Anderson eBooks")
    test_pdfs = list(pdf_dir.glob("*.pdf"))[:3]  # Test first 3 PDFs
    
    if not test_pdfs:
        print("❌ No test PDFs found")
        return
    
    print(f"\n📚 Testing with: {test_pdfs[0].name}")
    
    # Test each OCR method
    results = {}
    
    # Test Tesseract (current method)
    tesseract_time, tesseract_chars = test_tesseract_speed(test_pdfs[0])
    if tesseract_time:
        results['Tesseract (CPU)'] = tesseract_time
    
    # Test EasyOCR
    easyocr_time, easyocr_chars = test_easyocr_speed(test_pdfs[0])
    if easyocr_time:
        results['EasyOCR (GPU)'] = easyocr_time
    
    # Test PaddleOCR
    paddleocr_time, paddleocr_chars = test_paddleocr_speed(test_pdfs[0])
    if paddleocr_time:
        results['PaddleOCR (GPU)'] = paddleocr_time
    
    # Show comparison
    print("\n📊 SPEED COMPARISON RESULTS")
    print("=" * 50)
    
    if results:
        fastest_method = min(results.items(), key=lambda x: x[1])
        
        for method, time_taken in results.items():
            speedup = tesseract_time / time_taken if tesseract_time and method != 'Tesseract (CPU)' else 1.0
            status = "🏆" if method == fastest_method[0] else "⚡" if speedup > 1 else "🐌"
            
            print(f"{status} {method}: {time_taken:.2f}s (×{speedup:.1f} speedup)")
        
        print(f"\n🎯 RECOMMENDATION:")
        print(f"   Fastest method: {fastest_method[0]} ({fastest_method[1]:.2f}s)")
        
        if fastest_method[1] < tesseract_time:
            total_speedup = tesseract_time / fastest_method[1]
            new_total_time = 6 * 60 / total_speedup  # 6 hours in minutes
            print(f"   Total processing speedup: ×{total_speedup:.1f}")
            print(f"   Estimated new total time: {new_total_time:.0f} minutes ({new_total_time/60:.1f} hours)")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
