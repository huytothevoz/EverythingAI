import sys
import os
import time

def print_header():
    print("      PIXEL TANK WARS-  MENU")

def run_gui():
    print("\nĐang chạy.....")
    try:
        from gui import TankWarsGUI
        app = TankWarsGUI()
        app.run()
    except ImportError as e:
        print(f"Can't import gui.py. Chi tiết: {e}")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi chạy GUI: {e}")
    
    input("\nNhấn Enter để quay lại Menu...")

def run_benchmark():
    print_header()
    print("CHẠY THỬ NGHIỆM THUẬT TOÁN (BENCHMARK)")
    
    try:
        depth_str = input("Nhập độ sâu tìm kiếm (Depth) [Mặc định: 3]: ").strip()
        depth = int(depth_str) if depth_str else 3
        
        steps_str = input("Nhập số bước tối đa (Max Steps) [Mặc định: 1000]: ").strip()
        max_steps = int(steps_str) if steps_str else 1000
        
        print(f"\nĐang chạy Benchmark với Depth = {depth}, Max Steps = {max_steps}...")
        
        from experiment import BenchmarkExperiment
        experiment = BenchmarkExperiment(depth=depth, max_steps=max_steps)
        experiment.run_all_benchmarks()
        
    except ValueError:
        print("\nVui lòng nhập số nguyên hợp lệ!")
    except Exception as e:
        print(f"\nĐã xảy ra lỗi: {e}")
        
    input("\nNhấn Enter để quay lại Menu...")

def main_menu():
    while True:
        print_header()
        print(" 1. Chơi Game")
        print(" 2. Chạy Benchmark Thuật toán")
        print(" 0. Thoát chương trình")
        
        choice = input("Nhập lựa chọn của bạn (0-2): ").strip()
        
        if choice == '1':
            run_gui()
        elif choice == '2':
            run_benchmark()
        elif choice == '0':
            sys.exit(0)
        else:
            print("Lựa chọn không hợp lệ. Vui lòng thử lại!")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()