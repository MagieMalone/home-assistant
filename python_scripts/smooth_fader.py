#   smooth_fader.py
#   Version 2.0.1
#   By Ingrid Bakker studioilb.nl
#
#--------------------------------------
#
#  HOW TO CALL
#   service: python_script.smooth_fader
#   data:
#     entity_id: light.entity ; required
#     duration: '00:00:00' ; required, time under 10 seconds is not advised
#     brightness_start: 0-255 ; default: current
#     brightness_end: 0-255 ; default: current
#     brightness_curve: 'linear' or 'exp2' or 'exp5' or 'smooth' ; default: exp5
#     temperature_start: 154-370 ; default: current 
#     temperature_end: 154-370 ; default: current
#     temperature_curve: 'linear' or 'exp2' or 'exp5' or 'smooth' ; default: exp2
#
#  When light is off, and brighness_start or brighness_end is not defined, the light 
#  will remain off.
#  When light is off, and temperature_start or temperature_end is not defined, the
#  min/max mireds average will be default.
#
#  NOTES
#   adapted from https://community.home-assistant.io/t/light-fader-by-duration-time/99600
#   adapted from https://stackoverflow.com/questions/978599/equation-to-calculate-different-speeds-for-smooth-animation
#   FUNCTION: linear
#   round(start+direction*((x-1)*(difference/steps)+1))
#   50% effect a 50% of time
#   FUNCTION: exp2
#   n = 2, round(abs((direction*start)+(((difference^(1/n)-1)/(steps-1))*(x-1-1)+1)^n))
#   50% effect at 69% time
#   FUNCTION: exp5
#   n = 5, round(abs((direction*start)+(((difference^(1/n)-1)/(steps-1))*(x-1-1)+1)^n))
#   50% effect at 81% time
#   FUNCTION: slow
#   round(abs(direction*start+difference^(x/steps)))
#   50% effect at 88% time

# FOR debugging
debug_report = 0 # 0 = errors only; 1 = change events only; 2 = full
system_lag_time = 2 # Estimation how quick the a new state readout will be available.

# INPUT
entity_id = data.get ('entity_id')
duration = data.get ('duration')
b_start = int (data.get ('brightness_start', -1))
b_end = int (data.get ('brightness_end', -1))
b_curve = data.get ('brightness_curve', 'exp5')
t_start = int (data.get ('temperature_start', -1))
t_end = int (data.get ('temperature_end', -1))
t_curve = data.get ('temperature_curve', 'exp2')
if (debug_report > 1) : logger.info ("Curved fader: entity_id: %s, duration: %s, b_start: %s, b_end: %s, b_curve: %s, t_start: %s, t_end: %s, t_curve: %s", entity_id, duration, b_start, b_end, b_curve, t_start, t_end, t_curve)

# INPUT REQUIREMENTS
if ((entity_id is None) or (duration is None) or (max (b_end, t_end)==-1)) :
  logger.error ("Curved fader: Entity and duration are required, einther brightness_end or temperature_end should be defined")
else :
  duration = int (duration[:2]) * 3600 + int (duration[3:5]) * 60 + int (duration[-2:])
  # GET CURRENT STATE
  states = hass.states.get (entity_id)
  b_cur = b_initial = states.attributes.get ('brightness') or 0
  t_cur = t_initial = states.attributes.get ('color_temp') or 0
  if (b_start < 1 and b_end < 1) :
    logger.error ("Curved fader: When light is off or brighness_start and brighness_end is not defined or 0, the light will remain off, please define brightness")
  if (b_cur == 0 and t_start == -1) :
    logger.warning ("Curved fader: When light is off, and temperature_start is not defined, the min/max mireds average will be default, please define temperature_start.")
    t_cur = round ((states.attributes.get('min_mireds') + states.attributes.get('max_mireds')) / 2)

  if (b_start == -1) : b_start = b_cur
  if (b_end == -1) : b_end = b_start
  if (t_start == -1) : t_start = t_cur
  if (t_end == -1) : t_end = t_start
  if (debug_report > 1) : logger.info ("Curved fader: brightness current: %s, temperature current: %s", b_cur, t_cur)
  # MATH FOR CURVE
  curve = {}
  curve['linear'] = lambda x, steps, start, end, dif, dir : round (start + dir * ((x - 1) * (dif / steps) + 1))
  curve['exp2'] = lambda x, steps, start, end, dif, dir : round (abs ((dir * start) + (((dif ** (1 / 2) - 1) / (steps - 1)) * (x - 1 - 1) + 1) ** 2))
  curve['exp5'] = lambda x, steps, start, end, dif, dir : round (abs ((dir * start) + (((dif ** (1 / 5) - 1) / (steps - 1)) * (x - 1 - 1) + 1) ** 5))
  curve['smooth'] = lambda x, steps, start, end, dif, dir : round (abs (dir * start + dif ** (x / steps)))
  b_dif = abs (b_end - b_start)
  t_dif = abs (t_end - t_start)
  b_dir = t_dir = 1
  if (b_end < b_start) : b_dir = -1
  if (t_end < t_start) : t_dir = -1
  x = 0
  steps = max (1, b_dif, t_dif) # when no change is detected steps = 0, prevent error devide by zero
  step_time = duration / steps
  lag_steps_allowed = round (system_lag_time / step_time)

  if (debug_report > 1) : logger.info ("Curved fader: steps: %s, step_time: %s, lag_steps_allowed: %s", steps, step_time, lag_steps_allowed)
  if (debug_report > 1) : logger.info ("Curved fader: b_curve: %s, b_start: %s, b_end: %s, b_dif %s, b_dir %s, t_curve: %s, t_start: %s, t_end: %s, t_dif %s, t_dir %s", b_curve, b_start, b_end, b_dif, b_dir, t_curve, t_start, t_end, t_dif, t_dir)
  b_curve = curve[b_curve]
  t_curve = curve[t_curve]
  b_new = b_last = b_lag = b_start
  t_new = t_last = b_lag = t_start

  data = { "entity_id" : entity_id, "brightness" : b_new, "color_temp" : t_new }
  hass.services.call('light', 'turn_on', data)
  lag = {}
  lag[x] = {"b": b_new, "t": t_new}

  while (b_new != b_end) or (t_new != t_end) :
    x = x + 1
    xlag = max(0, x - lag_steps_allowed)
    if (x > 400) : # runtime protector
      logger.critical ('Curved fader: Break, runtime exceeded.')
      break
    if (b_dif > 0) : b_new = round(b_curve(x, steps, b_start, b_end, b_dif, b_dir))
    if (t_dif > 0) : t_new = round(t_curve(x, steps, t_start, t_end, t_dif, t_dir))
    lag[x] = {"b": b_new, "t": t_new}

    states = hass.states.get(entity_id)
    b_cur = states.attributes.get('brightness') or 0
    t_cur = states.attributes.get('color_temp') or 0

    #  Because the script runs synchronous and there is no button to stop a running
    #  python script, we need a break.
    #  For some reasone brightness under 25 is not registerd as an state, but it is
    #  visible in my light. So I do use it, but exclude it from this break. If you
    #  want to break the script, elevate the brightness above 25.
    #  In fast transitions the readout of the new state is to slow to check against.
    #  So when step_time < system_lag_time, break when current is not between lag
    # and last. Don't break when initial value is not changed yet.

    if (debug_report > 1) : logger.info("x: %s, b_cur: %s, b_last: %s, b_lag: %s, b_new: %s, t_cur: %s, t_last: %s, t_lag: %s, t_new: %s", x, b_cur, b_last, lag[xlag]["b"], b_new, t_cur, t_last, lag[xlag]["t"], t_new)
    if (x > 0 and b_cur > 24 and ((b_cur - lag[xlag]["b"]) * b_dir < 0 or (b_cur - b_last) * b_dir * -1 < 0 or (t_cur - lag[xlag]["t"]) * t_dir < 0 or (t_cur - t_last) * t_dir * -1 < 0) and b_cur != b_initial and t_cur != t_initial) :
      if ((b_cur - lag[xlag]["b"]) * b_dir < 0 or (t_cur - lag[xlag]["t"]) * t_dir < 0) :          
        logger.error ("Curved fader: Break because system_lag_time is set to low, please increase value. The lagere the difference between cur and lag, the larger the increment.")
        logger.error ("Lag_steps_allowed: %s, x: %s, b_cur: %s, b_lag: %s, t_cur: %s, t_lag: %s", lag_steps_allowed, x, b_cur, lag[xlag]["b"], t_cur, lag[xlag]["t"])
      else :
        logger.info ("Curved fader: Break by external change.")
      break

    if ((b_new != b_last) or (t_new != t_last)):
      data = { "entity_id" : entity_id, "brightness" : b_new, "color_temp" : t_new }
      hass.services.call('light', 'turn_on', data)
      if (debug_report > 0) : logger.info("Setting %s: brightness from %s to %s and color from %s to %s", entity_id, b_last, b_new, t_last, t_new)
      b_last = b_new
      t_last = t_new
    time.sleep(step_time)

logger.info ("Curved fader: finished.")