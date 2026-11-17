"""Run the unchanged scatter/FPS diagnostic on the two full-scan boundary rows."""
import m95_scatter_fps_same_input_20260925 as control


if __name__ == "__main__":
    control.TARGET_ROWS = (83, 174)
    control.main()
