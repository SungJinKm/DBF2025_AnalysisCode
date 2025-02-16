import pandas as pd
from vsp_grid import runVSPGridAnalysis
from mission_grid import runMissionGridSearch, ResultAnalysis
from mission_analysis import MissionAnalyzer
from vsp_analysis import removeAnalysisResults, loadAnalysisResults
from internal_dataclass import *
from setup_dataclass import *
import argparse

import cProfile
import pstats
from pstats import SortKey

def main():
    
    # Define parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--server_id", type=int, default=1, help="current server ID")
    parser.add_argument("--total_server", type=int, default=1, help="total server number")
    args = parser.parse_args()
    print(f"server ID : {args.server_id} , total server number : {args.total_server}\n")
    
    # Clear the path
    removeAnalysisResults(csvPath = "data/aircraft.csv")
    removeAnalysisResults(csvPath = "data/M2_total_results.csv")
    removeAnalysisResults(csvPath = "data/M3_total_results.csv")
    removeAnalysisResults(csvPath = "data/organized_results.csv")
    removeAnalysisResults(csvPath = "data/mission_statelog.csv")

    ## preset
    presetValues = PresetValues(
        m_x1 = 200,                         # g
        x1_time_margin = 10,                # sec
        
        throttle_takeoff = 0.9,             # 0~1
        max_climb_angle=40,                 #deg
        max_load = 30,                      # kg
        h_flap_transition = 5,              # m
        
        number_of_motor = 2,                 
        min_battery_voltage = 21.8,         # V 
        score_weight_ratio = 0.5            # mission2/3 score weight ratio (0~1)
        )
    
    propulsionSpecs = PropulsionSpecs(
        M2_propeller_data_path = "data/propDataCSV/PER3_8x6E.csv",
        M3_propeller_data_path = "data/propDataCSV/PER3_8x6E.csv",
        battery_data_path = "data/batteryDataCSV/Maxamps_2250mAh_6S.csv",
        Kv = 109.91,
        R = 0.062,
        number_of_battery = 2,
        n_cell = 6,
        battery_Wh = 49.95,
        max_current = 60,
        max_power = 1332    
    )
    
    aircraftParamConstraints = AircraftParamConstraints (
  
        span_min = 1800.0,                   # mm
        span_max = 1800.0,                   
        span_interval = 100.0,
    
        AR_min = 5.30,                  
        AR_max = 5.30,
        AR_interval = 0.05,
        
        taper_min = 0.65,
        taper_max = 0.65,                      
        taper_interval = 0.1,
        
        twist_min = 0.0,                     # degree
        twist_max = 0.0,                     
        twist_interval = 1.0,
        
        # airfoil_list = ['sg6043','mh122','s4062','s9027','hq3010','hq3011']
        airfoil_list = ['s4062', 's9027']
        )
    
    aerodynamicSetup = AerodynamicSetup(
        alpha_start = -3,
        alpha_end = 10,
        alpha_step = 1,
        fuselage_cross_section_area = 19427,    ##mm2
        fuselage_Cd_datapath = "data/fuselageDragCSV/fuselageDragCoefficients.csv",
        AOA_stall = 13,
        AOA_takeoff_max = 10,
        AOA_climb_max = 8,
        AOA_turn_max = 8  
    )
    baseAircraft = Aircraft(
        m_fuselage = 3000,
        wing_area_blocked_by_fuselage = 72640,    #mm2
        wing_density = 0.0000852,

        mainwing_span = 1800,        
        mainwing_AR = 5.45,           
        mainwing_taper = 0.65,        
        mainwing_twist = 0.0,        
        mainwing_sweepback = 0,   
        mainwing_dihedral = 5.0,     
        mainwing_incidence = 0.0,    

        flap_start = [0.05, 0.4],            
        flap_end = [0.25, 0.6],              
        flap_angle = [20.0, 20.0],           
        flap_c_ratio = [0.35, 0.35],         

        horizontal_volume_ratio = 0.7,
        horizontal_area_ratio = 0.25, 
        horizontal_AR = 4.0,         
        horizontal_taper = 1,      
        horizontal_ThickChord = 8,

        vertical_volume_ratio = 0.053,
        vertical_taper = 0.6,        
        vertical_ThickChord = 9,  
        
        mainwing_airfoil_datapath = "data/airfoilDAT/e64.dat",
        horizontal_airfoil_datapath= "data/airfoilDAT/naca0008.dat",
        vertical_airfoil_datapath= "data/airfoilDAT/naca0009.dat"
        
        )

    runVSPGridAnalysis(aircraftParamConstraints,aerodynamicSetup, presetValues,baseAircraft,args.server_id, args.total_server)

    results = pd.read_csv("data/aircraft.csv", sep='|', encoding='utf-8')
    print(results.head()) 

    for hashVal in results["hash"]:
        print(f"\nAnalyzing for hash{hashVal}")

        missionParamConstraints = MissionParamConstraints (
            
            MTOW_min = 7,
            MTOW_max = 8,
            MTOW_analysis_interval = 0.5,
            
            M2_max_speed_min = 35,
            M2_max_speed_max = 35,
            M3_max_speed_min = 30,
            M3_max_speed_max = 30,
            max_speed_analysis_interval = 2,
            
            #Constraints for calculating mission2
            M2_climb_thrust_ratio_min = 0.9,
            M2_climb_thrust_ratio_max = 0.9,
            M2_turn_thrust_ratio_min = 0.7,
            M2_turn_thrust_ratio_max = 0.8,
            M2_level_thrust_ratio_min = 0.7,
            M2_level_thrust_ratio_max = 0.7,
            M2_thrust_analysis_interval = 0.05,

            #Constraints for calculating mission3  
            M3_climb_thrust_ratio_min = 0.9,
            M3_climb_thrust_ratio_max = 0.9,
            M3_turn_thrust_ratio_min = 0.5,
            M3_turn_thrust_ratio_max = 0.6,
            M3_level_thrust_ratio_min = 0.6,
            M3_level_thrust_ratio_max = 0.6,
            M3_thrust_analysis_interval = 0.05,
            
            wing_loading_min = 5,
            wing_loading_max = 15
            )
        
        runMissionGridSearch(hashVal,presetValues,missionParamConstraints,propulsionSpecs)
          
    
    ResultAnalysis(presetValues)

    return

def main2(a):

    
    ## preset
    presetValues = PresetValues(
        m_x1 = 200,                         # g
        x1_time_margin = 10,                # sec
        
        throttle_takeoff = 0.9,             # 0~1
        max_climb_angle=40,                 #deg
        max_load = 30,                      # kg
        h_flap_transition = 5,              # m
        
        number_of_motor = 2,                 
        min_battery_voltage = 21.8,         # V 
        score_weight_ratio = 0.5            # mission2/3 score weight ratio (0~1)
        )
    
    propulsionSpecs = PropulsionSpecs(
        M2_propeller_data_path = "data/propDataCSV/PER3_8x6E.csv",
        M3_propeller_data_path = "data/propDataCSV/PER3_8x6E.csv",
        battery_data_path = "data/batteryDataCSV/Maxamps_2250mAh_6S.csv",
        Kv = 109.91,
        R = 0.062,
        number_of_battery = 2,
        n_cell = 6,
        battery_Wh = 49.95,
        max_current = 60,
        max_power = 1332    
    )
    param = MissionParameters(
        max_speed= 40,                       # Fixed
        max_load_factor = 4.0,               # Fixed
        m_takeoff = 6,
        climb_thrust_ratio = 0.9,
        level_thrust_ratio = 0.5,
        turn_thrust_ratio = 0.5,               
        propeller_data_path = "data/propDataCSV/PER3_8x6E.csv", 
    )
        
    propulsionSpecs = PropulsionSpecs(
        M2_propeller_data_path = "data/propDataCSV/PER3_10x6E.csv",
        M3_propeller_data_path = "data/propDataCSV/PER3_10x6E.csv",
        battery_data_path = "data/batteryDataCSV/Maxamps_2250mAh_6S.CSV",
        Kv = 109.91,
        R = 0.062,
        number_of_battery = 2,
        n_cell = 6,
        battery_Wh = 49.95,
        max_current = 60,
        max_power = 1332    
    )
        
    missionAnalyzer = MissionAnalyzer(a, param, presetValues, propulsionSpecs)
    missionAnalyzer.run_mission2()
    missionAnalyzer.run_mission3()

if __name__== "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    
    a=loadAnalysisResults('2843180587264577993')
    # Run the function
    main2(a)
    main2(a)
    main2(a)
    main2(a)
    profiler.disable()
    
    # Print stats sorted by cumulative time
    stats = pstats.Stats(profiler)
    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_stats(40)  # Show top 20 time-consuming lines
