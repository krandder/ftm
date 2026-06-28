# Execute from the root directory of the repo with  
#   python -m website.gen

# I should automate the whole process...

import re
import json
from ftm.core.utils import *
from ftm.core.model import *
from ftm.core.scenarios import *

important_params_and_metrics = pd.read_excel(
    get_input_workbook(),
    sheet_name = MOST_IMPORTANT_PARAMETERS_SHEET
)
important_params = important_params_and_metrics['Parameter id'].tolist()

LOGNORMAL_TASK_DISTRIBUTION_PARAMETER = 'use_lognormal_task_distribution'
LOGNORMAL_TASK_DISTRIBUTION_NAME = 'Use lognormal 99% task distribution'
LOGNORMAL_TASK_DISTRIBUTION_MEANING = (
  'If enabled, task thresholds are generated from a lognormal distribution: '
  'the full automation requirement is treated as the 99th percentile task '
  'threshold, the 20th percentile is pinned by the FLOP gap, and the default '
  '100 task buckets are given unequal masses to resolve the 99%-99.9% tail.'
)
LOGNORMAL_TASK_DISTRIBUTION_JUSTIFICATION = (
  'Experimental alternative to the hardcoded FTM task quantile curve; useful '
  'for inspecting 99%-99.9%-100% tail behavior.'
)

EXTRA_METRIC_NAMES = {
  'automation_gns_99%': '99% automation year',
  'automation_gns_99.9%': '99.9% automation year',
  'automation_rnd_99%': '99% R&D automation year',
  'automation_rnd_99.9%': '99.9% R&D automation year',
}

EXTRA_METRIC_MEANINGS = {
  'automation_gns_99%': 'Year when AI has automated 99% of goods and services tasks.',
  'automation_gns_99.9%': 'Year when AI has automated 99.9% of goods and services tasks.',
  'automation_rnd_99%': 'Year when AI has automated 99% of R&D tasks (in software and hardware).',
  'automation_rnd_99.9%': 'Year when AI has automated 99.9% of R&D tasks (in software and hardware).',
}

def generate_sidebar_content():
  parameter_table = get_parameter_table(tradeoff_enabled=True)
  best_guess_parameters = {parameter : row['Best guess'] for parameter, row in parameter_table.iterrows()}
  param_names = get_param_names()

  test = 0
  important_parameters = []
  extra_parameters = []
  for param, value in best_guess_parameters.items():
    name = param_names[param]
    array = important_parameters if param in important_params else extra_parameters

    classes = 'input-parameter'
    additional_inputs = ''
    label_target = param

    if param in ['runtime_training_tradeoff', 'runtime_training_max_tradeoff']:
      enabled = best_guess_parameters['runtime_training_tradeoff'] > 0
      if not enabled:
        classes += ' disabled'
      id = "runtime_training_tradeoff_enabled_1" if param == 'runtime_training_tradeoff' else "runtime_training_tradeoff_enabled_2"
      additional_inputs += f' <input id="{id}" class="runtime_training_tradeoff_enabled" {"checked" if enabled else ""} type="checkbox">'
      label_target = id

    if param == 'runtime_training_tradeoff' and value < 0:
      value = 1

    array.append(f'''<div class="{classes}"><label for="{label_target}">{name}</label>{additional_inputs} <input class="input" id="{param}" value="{prettify_float(value)}"></div>''')
    test += 1

  extra_parameters.append(
    f'''<div class="input-parameter"><label for="{LOGNORMAL_TASK_DISTRIBUTION_PARAMETER}">{LOGNORMAL_TASK_DISTRIBUTION_NAME}</label> <input class="input" id="{LOGNORMAL_TASK_DISTRIBUTION_PARAMETER}" type="checkbox"></div>'''
  )

  # Basic params
  for p in important_parameters:
    print(p)

  # Extra params
  print('''
  <div class="handorgel additional-parameters">
    <h3 class="handorgel__header">
      <div class="handorgel__header__button" autofocus>
        Show additional parameters
        <span class="icon bi bi-plus-lg"></span>
      </div>
    </h3>
    <div class="handorgel__content">
''' + ('\n'.join(extra_parameters)) + '''
    </div>
  </div>
  ''')

def prettify_float(x):
  sign = -1 if (x < 0) else +1;
  if sign < 0: x = -x;

  if x == 0:
    s = '0'
  elif x > 100 or x < 1e-4:
    s = f'{x:.4e}'
  else:
    s = f'{x:.4}'

  s = re.sub(r'\.([0-9]*[1-9])?0*', r'.\1', s); # remove trailing zeroes
  s = re.sub(r'e([+-]?)0*([0-9])', r'e\1\2', s); # remove leading zeroes in the exponential
  s = s.replace('e+', 'e')
  s = s.replace('.e', 'e') # remove the decimal point, if no decimal
  s = re.sub(r'\.$', '', s) # remove the decimal point, if no decimal

  if sign < 0: s = '-' + s;

  return s

def generate_dictionaries():
  parameter_names = get_param_names()
  parameter_names[LOGNORMAL_TASK_DISTRIBUTION_PARAMETER] = LOGNORMAL_TASK_DISTRIBUTION_NAME
  parameter_meanings = get_parameters_meanings()
  parameter_meanings[LOGNORMAL_TASK_DISTRIBUTION_PARAMETER] = LOGNORMAL_TASK_DISTRIBUTION_MEANING
  parameter_justifications = get_parameter_justifications()
  parameter_justifications[LOGNORMAL_TASK_DISTRIBUTION_PARAMETER] = LOGNORMAL_TASK_DISTRIBUTION_JUSTIFICATION

  print(f'let parameter_names = {json.dumps(parameter_names)};')
  print(f'let parameter_meanings = {json.dumps(parameter_meanings)};')
  print(f'let parameter_justifications = {json.dumps(parameter_justifications)};')
  metric_names = get_metric_names()
  metric_names.update(EXTRA_METRIC_NAMES)
  metric_meanings = get_metrics_meanings()
  metric_meanings.update(EXTRA_METRIC_MEANINGS)

  print(f'let metric_names = {json.dumps(metric_names)};')
  print(f'let metric_meanings = {json.dumps(metric_meanings)};')

  print(f'let variable_names = {json.dumps(get_variable_names())};')

  print()

  parameter_table = get_parameter_table(tradeoff_enabled=True)

  best_guess_parameters = {parameter : row['Best guess'] for parameter, row in parameter_table.iterrows()}

  conservative_parameters = {
    parameter: row['Conservative'] if not np.isnan(row['Aggressive']) else row['Best guess'] for parameter, row in parameter_table.iterrows()
  }

  aggressive_parameters = {
    parameter: row['Aggressive'] if not np.isnan(row['Aggressive']) else row['Best guess'] for parameter, row in parameter_table.iterrows()
  }

  def handle_tradeoff(params):
    params['runtime_training_tradeoff_enabled'] = (params['runtime_training_tradeoff'] > 0)
    params[LOGNORMAL_TASK_DISTRIBUTION_PARAMETER] = False
    return params

  print(f'let conservative_parameters = {json.dumps(handle_tradeoff(conservative_parameters))};')
  print(f'let best_guess_parameters = {json.dumps(handle_tradeoff(best_guess_parameters))};')
  print(f'let aggressive_parameters = {json.dumps(handle_tradeoff(aggressive_parameters))};')

  log.level = Log.ERROR_LEVEL

  scenario_runner = ScenarioRunner()
  groups = scenario_runner.simulate_all_scenarios()

  parameters = {group.name: scenario.params for group in groups for scenario in group.scenarios if scenario.name == 'Best guess'}
  print()
  print(f'let short_timelines_best_guess = {json.dumps(handle_tradeoff(parameters["Very short timelines"]))};')
  print(f'let med_timelines_best_guess = {json.dumps(handle_tradeoff(parameters["Med timelines"]))};')
  print(f'let long_timelines_best_guess = {json.dumps(handle_tradeoff(parameters["Very long timelines"]))};')

def generate_arrays():
  print(f'let important_metrics = {json.dumps([x for x in important_params_and_metrics["Metric id"] if not pd.isnull(x)])};')

if __name__ == '__main__':
  # Handle CLI arguments
  parser = init_cli_arguments()
  args = handle_cli_arguments(parser)

  generate_sidebar_content()
  print()
  generate_dictionaries()
  print()
  generate_arrays()
