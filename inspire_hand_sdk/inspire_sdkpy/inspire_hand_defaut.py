

from .inspire_dds import inspire_hand_touch,inspire_hand_ctrl,inspire_hand_state
import threading
modbus_lock = threading.Lock()

# Data definitions   
data_sheet = [
    ("Pinky Tip Touch", 3000, 18, (3, 3), "fingerone_tip_touch"),           # Pinky fingertip touch
    ("Pinky Top Touch", 3018, 192, (12, 8), "fingerone_top_touch"),         # Pinky fingertip top touch
    ("Pinky Palm Touch", 3210, 160, (10, 8), "fingerone_palm_touch"),       # Pinky palm touch
    ("Ring Tip Touch", 3370, 18, (3, 3), "fingertwo_tip_touch"),            # Ring fingertip touch
    ("Ring Top Touch", 3388, 192, (12, 8), "fingertwo_top_touch"),          # Ring fingertip top touch
    ("Ring Palm Touch", 3580, 160, (10, 8), "fingertwo_palm_touch"),        # Ring palm touch
    ("Middle Tip Touch", 3740, 18, (3, 3), "fingerthree_tip_touch"),        # Middle fingertip touch
    ("Middle Top Touch", 3758, 192, (12, 8), "fingerthree_top_touch"),      # Middle fingertip top touch
    ("Middle Palm Touch", 3950, 160, (10, 8), "fingerthree_palm_touch"),    # Middle palm touch
    ("Index Tip Touch", 4110, 18, (3, 3), "fingerfour_tip_touch"),          # Index fingertip touch
    ("Index Top Touch", 4128, 192, (12, 8), "fingerfour_top_touch"),        # Index fingertip top touch
    ("Index Palm Touch", 4320, 160, (10, 8), "fingerfour_palm_touch"),      # Index palm touch
    ("Thumb Tip Touch", 4480, 18, (3, 3), "fingerfive_tip_touch"),          # Thumb fingertip touch
    ("Thumb Top Touch", 4498, 192, (12, 8), "fingerfive_top_touch"),        # Thumb fingertip top touch
    ("Thumb Middle Touch", 4690, 18, (3, 3), "fingerfive_middle_touch"),    # Thumb middle touch
    ("Thumb Palm Touch", 4708, 192, (12, 8), "fingerfive_palm_touch"),      # Thumb palm touch
    ("Palm Touch", 4900, 224, (14, 8), "palm_touch")                        # Palm touch
]
status_codes = {
    0: "Releasing",
    1: "Grasping",
    2: "Position Reached",
    3: "Force Limit Reached",
    5: "Current Protection Stop",
    6: "Actuator Stall Stop",
    7: "Actuator Fault Stop",
    255: "Error"
}
error_descriptions = {
    0: "Stall Fault",
    1: "Overtemperature Fault",
    2: "Overcurrent Fault",
    3: "Motor Abnormal",
    4: "Communication Fault"
}
def get_error_description(error_value):
    error_reasons = []
    # 检查每一位是否为1，如果为1则添加对应的故障说明
    for bit, description in error_descriptions.items():
        if error_value & (1 << bit):  # 使用位运算检查对应位是否为1
            error_reasons.append(description)
    return error_reasons

# Print combined fault reasons
def update_error_label(ERROR):
    error_summary = []
    for e in ERROR:
        binary_error = '{:04b}'.format(int(e))  # Convert to 4-bit binary representation
        error_reasons = get_error_description(int(e))  # Get fault reason list
        if error_reasons:
            error_summary.append(f"ERROR {e} ({binary_error}): " + ', '.join(error_reasons))
        else:
            error_summary.append(f"ERROR {e} ({binary_error}): No Fault")
    # Update label content
    # print("\n".join(error_summary))
    return"\t".join(error_summary)
       
       
 
def get_inspire_hand_touch():
    return inspire_hand_touch(
        fingerone_tip_touch=[0 for _ in range(9)],        # 小拇指指端触觉数据
        fingerone_top_touch=[0 for _ in range(96)],       # 小拇指指尖触觉数据
        fingerone_palm_touch=[0 for _ in range(80)],      # 小拇指指腹触觉数据
        fingertwo_tip_touch=[0 for _ in range(9)],        # 无名指指端触觉数据
        fingertwo_top_touch=[0 for _ in range(96)],       # 无名指指尖触觉数据
        fingertwo_palm_touch=[0 for _ in range(80)],      # 无名指指腹触觉数据
        fingerthree_tip_touch=[0 for _ in range(9)],      # 中指指端触觉数据
        fingerthree_top_touch=[0 for _ in range(96)],     # 中指指尖触觉数据
        fingerthree_palm_touch=[0 for _ in range(80)],    # 中指指腹触觉数据
        fingerfour_tip_touch=[0 for _ in range(9)],       # 食指指端触觉数据
        fingerfour_top_touch=[0 for _ in range(96)],      # 食指指尖触觉数据
        fingerfour_palm_touch=[0 for _ in range(80)],     # 食指指腹触觉数据
        fingerfive_tip_touch=[0 for _ in range(9)],       # 大拇指指端触觉数据
        fingerfive_top_touch=[0 for _ in range(96)],      # 大拇指指尖触觉数据
        fingerfive_middle_touch=[0 for _ in range(9)],    # 大拇指指中触觉数据
        fingerfive_palm_touch=[0 for _ in range(96)],     # 大拇指指腹触觉数据
        palm_touch=[0 for _ in range(112)]                # 掌心触觉数据
    )
    
def get_inspire_hand_state():
    return inspire_hand_state(
        pos_act=[0 for _ in range(6)],        # 小拇指指端触觉数据
        angle_act=[0 for _ in range(6)],       # 小拇指指尖触觉数据
        force_act=[0 for _ in range(6)],      # 小拇指指腹触觉数据
        current=[0 for _ in range(6)],        # 无名指指端触觉数据
        err=[0 for _ in range(6)],        # 无名指指端触觉数据
        status=[0 for _ in range(6)],        # 无名指指端触觉数据
        temperature=[0 for _ in range(6)],        # 无名指指端触觉数据
    ) 

def get_inspire_hand_ctrl():
    return inspire_hand_ctrl(
        pos_set=[0 for _ in range(6)],        # 小拇指指端触觉数据
        angle_set=[0 for _ in range(6)],       # 小拇指指尖触觉数据
        force_set=[0 for _ in range(6)],      # 小拇指指腹触觉数据
        speed_set=[0 for _ in range(6)],        # 无名指指端触觉数据
        mode=0b0000
    ) 

defaut_ip='192.168.11.210'