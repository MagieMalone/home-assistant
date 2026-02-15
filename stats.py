import pandas as pd
import sqlite3
import pandas as pd

con = sqlite3.connect("home-assistant_v2.db")

def update_id(old_sensor_id, new_sensor_id, table):
    assert table in ["statistics", "statistics_short_term", "states"]

#    log.warning(f"Updating {old_sensor_id} to {new_sensor_id} in {table}")

    try:

        if table == "states":
            # States
            ts_field = "last_updated_ts"

            old_meta_id = pd.read_sql_query(f"""SELECT metadata_id 
                                                FROM states_meta
                                                WHERE entity_id = '{old_sensor_id}';""", con).loc[0,"metadata_id"]
            
            new_meta_id = pd.read_sql_query(f"""SELECT metadata_id 
                                                FROM states_meta
                                                WHERE entity_id = '{new_sensor_id}';""", con).loc[0,"metadata_id"]
        else:
            # Statistics
            ts_field = "start_ts"

            old_meta_id = pd.read_sql_query(f"""SELECT id 
                                                FROM statistics_meta
                                                WHERE statistic_id = '{old_sensor_id}';""", con).loc[0,"id"]   
            
            new_meta_id = pd.read_sql_query(f"""SELECT id 
                                                FROM statistics_meta
                                                WHERE statistic_id = '{new_sensor_id}';""", con).loc[0,"id"]

        new_ts_min = pd.read_sql_query(f"""SELECT MIN({ts_field}) as ts_min 
                                        FROM {table} 
                                        WHERE metadata_id = '{new_meta_id}';""", con).loc[0,"ts_min"]
            
        stmnt = f"""UPDATE {table} 
            SET metadata_id = {new_meta_id}
            WHERE metadata_id = {old_meta_id}
            AND {ts_field} < {new_ts_min}
            """
        
        cur = con.cursor()
        cur.execute(stmnt)
        con.commit()    

    except Exception as e:
#        log.warning(e)
        pass

# mapping of the sensors, statistics of the left ones will be merged into the right ones
mapping={
    "sensor.toon_gas_used_cnt_2": "sensor.toon_smart_meter_gas_used_cnt",
    "sensor.toon_p1_power_use_low_2": "sensor.toon_smart_meter_p1_power_use_low",
    "sensor.toon_p1_power_use_high_2": "sensor.toon_smart_meter_p1_power_use_high",
    "sensor.toon_p1_power_prod_low_2": "sensor.toon_smart_meter_p1_power_prod_low",
    "sensor.toon_p1_power_prod_high_2": "sensor.toon_smart_meter_p1_power_prod_high",
    "sensor.toon_p1_power_use_cnt_low_2": "sensor.toon_smart_meter_p1_power_use_cnt_low",
    "sensor.toon_p1_power_use_cnt_high_2": "sensor.toon_smart_meter_p1_power_use_cnt_high",
    "sensor.toon_p1_power_prod_cnt_low_2": "sensor.toon_smart_meter_p1_power_prod_cnt_low",
    "sensor.toon_p1_power_prod_cnt_high_2": "sensor.toon_smart_meter_p1_power_prod_cnt_high",
    "sensor.toon_p1_power_use_cnt_low_cost_2": "sensor.toon_smart_meter_p1_power_use_cnt_low_cost",
    "sensor.toon_gas_used_cnt_cost_2": "sensor.toon_smart_meter_p1_power_use_cnt_high_cost",
    "sensor.toon_p1_power_use_cnt_high_cost_2": "sensor.toon_smart_meter_gas_used_cnt_cost"
    }

for old_sensor_id, new_sensor_id in mapping.items():
    for table in ["statistics", "statistics_short_term", "states"]:  
        update_id(old_sensor_id, new_sensor_id, table)
