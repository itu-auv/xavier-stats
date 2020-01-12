#!/usr/bin/env python
import subprocess
import rospy
from std_msgs.msg import String, Float32
from xavier_stats.msg import XavierStatus

rospy.init_node("xavier_status_node", anonymous=True)

def runProcess(exe):
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        # returns None while subprocess is running
        retcode = p.poll()
        line = p.stdout.readline()
        yield line
        if retcode is not None:
            break


interval = rospy.get_param("~interval")
pub = rospy.Publisher("/turquoise/xavier/stats", XavierStatus, queue_size=10)
pub_gputemp = rospy.Publisher("/turquoise/xavier/gpu_temp", Float32, queue_size=10)
pub_cputemp = rospy.Publisher("/turquoise/xavier/cpu_temp", Float32, queue_size=10)
pub_boardtemp = rospy.Publisher("/turquoise/xavier/board_temp", Float32, queue_size=10)
pub_auxtemp = rospy.Publisher("/turquoise/xavier/aux_temp", Float32, queue_size=10)

# pub_ram = rospy.Publisher("/turquoise/xavier/ram", Float32, queue_size=10)

# data: "RAM 2336/15827MB (lfb 2948x4MB) CPU [2%@1190,1%@1190,0%@1190,0%@1190,off,off,off,off]\
#   \ EMC_FREQ 0% GR3D_FREQ 0% AO@25.5C GPU@26C Tboard@27C Tdiode@28.75C AUX@25C CPU@27C\
#   \ thermal@25.75C PMIC@100C GPU 465/465 CPU 310/310 SOC 1242/1242 CV 0/0 VDDRQ 0/0\
#   \ SYS5V 1776/1776\n"
# ---


for line in runProcess(('tegrastats --interval ' + str(interval)).split()):
    if not rospy.is_shutdown():
        msg = XavierStatus()
        msg.header.stamp = rospy.Time.now()
        raw_data = line.split(" ")

        msg.ram = int(raw_data[1].split("/")[0])
        msg.cpu_usage = [int(x.replace("off", "0%@0").split("%@")[0]) for x in raw_data[5][1:-1].split(",")]
        msg.cpu_clock = [int(x.replace("off", "0%@0").split("%@")[1]) for x in raw_data[5][1:-1].split(",")]

        for raw in raw_data:
            if "GPU@" in raw:
                msg.gpu_temp = float(raw.split("GPU@")[1].split("C")[0])
            if "Tboard@" in raw:
                msg.board_temp = float(raw.split("Tboard@")[1].split("C")[0])
            if "Tdiode@" in raw:
                msg.diode_temp = float(raw.split("Tdiode@")[1].split("C")[0])
            if "AUX@" in raw:
                msg.aux_temp = float(raw.split("AUX@")[1].split("C")[0])
            if "CPU@" in raw:
                msg.cpu_temp = float(raw.split("CPU@")[1].split("C")[0])
            if "thermal@" in raw:
                msg.thermal_temp = float(raw.split("thermal@")[1].split("C")[0])
        msg.raw = line

        pub.publish(msg)

        pub_gputemp.publish(Float32(msg.gpu_temp))
        pub_cputemp.publish(Float32(msg.cpu_temp))
        pub_boardtemp.publish(Float32(msg.board_temp))
        pub_auxtemp.publish(Float32(msg.aux_temp))
    else:
        break
