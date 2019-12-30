import jinja2
import ruamel.yaml
import os
import codecs

template_file = "switch_yaml.j2"
yaml_parameter_file = "parameters.yaml"
output_directory = "_output"

# read the contents from the YAML files
print("Read YAML parameter file...")
yaml = ruamel.yaml.YAML(typ='safe')
config_parameters = yaml.load(open(yaml_parameter_file))

# next we need to create the central Jinja2 environment and we will load
# the Jinja2 template file (the two parameters ensure a clean output in the
# configuration file)
print("Create Jinja2 environment...")
env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="."),
                         trim_blocks=True,
                         lstrip_blocks=True)
template = env.get_template(template_file)

# we will make sure that the output directory exists
if not os.path.exists(output_directory):
    os.mkdir(output_directory)

# now create the templates
print("Create templates...")
for parameter in config_parameters:
    result = template.render(parameter)
    with  codecs.open(os.path.join(output_directory, parameter['switchname'] + ".yaml"), "w", "utf-8") as f:
    	f.write(result)
    	f.close()
    print("Configuration '%s' created..." % (parameter['switchname'] + ".yaml"))
print("DONE")
