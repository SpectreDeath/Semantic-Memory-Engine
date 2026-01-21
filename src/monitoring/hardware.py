from mcp.server.fastmcp import FastMCP
import psutil
import pynvml

mcp = FastMCP("BasementMonitor")

@mcp.tool()
def get_thermal_stats() -> str:
    """Checks the laptop health in the cold basement."""
    cpu = psutil.cpu_percent(interval=0.1)
    
    gpu_info = "GPU: Not Detected"
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        
        # Calculate how much "room" we have in the cold
        margin = 80 - temp 
        
        gpu_info = (
            f"GPU Temp: {temp}°C\n"
            f"Thermal Margin: {margin}°C until throttle\n"
            f"VRAM: {mem.used // 1024**2}MB / {mem.total // 1024**2}MB"
        )
        pynvml.nvmlShutdown()
    except:
        gpu_info = "GPU: Error accessing NVML"

    return f"--- HARDWARE STATUS ---\nCPU: {cpu}%\n{gpu_info}"

if __name__ == "__main__":
    mcp.run()