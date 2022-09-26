import json
import os
import graphviz
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--path',nargs=1,default='', help='Path to report (*.json)')
parser.add_argument('--out',nargs='?',default='./',help='Path to result folder')

args = parser.parse_args()

directory = args.out
directory += "Reports"
if not os.path.exists(directory):
    os.makedirs(directory)

def create_csv(name,data_list,directory=directory):
    with open("{}/{}.csv".format(directory,name),'w') as output_csv:
        for cur_line in data_list:
            output_csv.writelines(cur_line)
            output_csv.writelines("\n")

#path_to_json_report = 
if args.path == '':
    print("\n")
    print("The path is not defined!")
    raise SystemExit
else:
    path_to_json_report = args.path[0]

with open(path_to_json_report,'r') as input_json:
    json_data = json.load(input_json)

#dict_keys(['Package', 'CreatedTimestamp', 'Analysis'])
#Analysis - dict_keys(['import', 'install'])
#Package - dict_keys(['Name', 'Version', 'Ecosystem'])
#install - dict_keys(['Status', 'Stdout', 'Stderr', 'Files', 'Sockets', 'Commands', 'DNS'])

package_name = json_data['Package']['Name']
print("Package Name:", package_name)
print("Package Ecosystem: ", json_data['Package']['Ecosystem'])

#Import files
report_import_list = []
report_import_list.append("Path,Read,Write,Delete")
for cur_dict in json_data["Analysis"]["import"]["Files"]:
    buffer_str = ""
    for cur_key in cur_dict:
        buffer_str += str(cur_dict[cur_key])
        buffer_str += ","
    buffer_str.rstrip(",")
    report_import_list.append(buffer_str)

#Install requests
report_sockets_list = []
report_sockets_list.append("Address,Port,Hostnames")
for cur_dict in json_data["Analysis"]["install"]["Sockets"]:
    buffer_str = ""
    for cur_key in cur_dict:
        if isinstance(cur_dict[cur_key],list) and len(cur_dict[cur_key]):
            buffer_str += str(cur_dict[cur_key][0])
        else:
            buffer_str += str(cur_dict[cur_key])
        buffer_str.replace(',','.')
        buffer_str += ","
    buffer_str.rstrip(",")
    report_sockets_list.append(buffer_str)

#Install commands
report_commands_list = []
report_commands_list.append("Commands")
for cur_dict in json_data["Analysis"]["install"]["Commands"]:
    buffer_str = " ".join(cur_dict["Command"])
    #print(cur_dict)
    buffer_str.rstrip(",")
    report_commands_list.append(buffer_str)

#Install DNS Queries
report_DNS_list = []
report_DNS_list.append("Class,Hostname")

for cur_dict in json_data["Analysis"]["install"]["DNS"]:
    buffer_str = ""
    buffer_str += cur_dict["Class"]
    buffer_str += ","
    for cur_quer in cur_dict["Queries"]:
        buffer_str += cur_quer["Hostname"]
        buffer_str += ","
    buffer_str.rstrip(",")
    report_DNS_list.append(buffer_str)

#Install files r/w/d
report_files_list = []
report_files_list.append("Path,Read,Write,Delete")
buffer_str = ""
for cur_dict in json_data["Analysis"]["install"]["Files"]:
    buffer_str = ""
    for cur_key in cur_dict:
        buffer_str += str(cur_dict[cur_key])
        buffer_str += ","
    buffer_str.rstrip(",")
    report_files_list.append(buffer_str)

#Create CSV reports
create_csv("import_report",report_import_list)
create_csv("files_report",report_files_list)
create_csv("commands_report",report_commands_list)
create_csv("DNS_report",report_DNS_list)
create_csv("sockets_report",report_sockets_list)

#Graph for files create
files_graph_list = []
for i in report_files_list:
    buf = i.split(',')[0]
    result = ""
    try:
        if len(buf.split('/')) > 6:
            result = "/".join(buf.split('/')[:-3])
        elif len(buf.split('/')) <= 6 and len(buf.split('/')) > 3:
            result = "/".join(buf.split('/')[:-2]) 
        else:
            if result != '.' and result != "Path" and result != "":
                result = buf
    except:
        if result != '':
            result = buf
    
    if result not in files_graph_list and result != "":
        files_graph_list.append(result)

print("Nodes for files:",len(files_graph_list))
print("Rendering...")

dot = graphviz.Digraph(comment='The Graph', engine='fdp', graph_attr={'splines': 'true'}, node_attr={'shape': 'box'})
dot.center=""
dot.attr(size='1000,1000')
dot.node(package_name, shape='Mdiamond', color='red')

for file in files_graph_list:
    try:
        dot.edge(package_name,file,constraint='false')
    except Exception as e:
        print(e)

dot.format = 'png'
try:
    dot.render("{}/files_graph".format(directory))
except Exception as e:
    print("Oops! Its wrong input data! Maybe graph is too large..")
    print(e)

#Graph for requests
#edge_attr={'mindist':'0.0'} - circo only
#graph_attr={'splines': 'ortho'}
dot_rquests = graphviz.Digraph(comment='The Graph', engine='circo', graph_attr={'splines': 'line', 'rankdir':"LR"}, node_attr={'shape': 'box'})
dot_rquests.center=""
dot_rquests.node(package_name, shape='Mdiamond', color='red')
len_list= len(report_sockets_list)-1
print("Nodes for requests", len_list)
print("Rendering...")
for cur_line in report_sockets_list[-len_list:]:
    line = cur_line.split(',')
    try:
        ip_buffer = line[0]
        #Catch exception: ':' in edges name 
        if ip_buffer.__contains__(':'):
            dot_rquests.body.append('\t"{}" -> "{}" [label={} constraint=false]\n'.format(package_name, ip_buffer, line[1])) #input edge in graph body
        else:
            dot_rquests.edge(package_name,ip_buffer, constraint='false',label=line[1]) #create edge 
    except Exception as e:
        print("Oops! Edge was not created...")
        print(e)

dot_rquests.format = 'png'
try:
    dot_rquests.render("{}/requests_graph".format(directory))
except Exception as e:
    print("Oops! Incorrect input data! Maybe graph is too large..")
    print(e)