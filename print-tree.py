import csv
import argparse

HIGHLIGHT_FONT_COLOR = 'blue'
HIGHLIGHT_NODE_COLOR = 'blue'
HIGHLIGHT_EDGE_COLOR = 'blue'

people = {}
partners = {}
next_person_id = 0
next_partners_id = 0

def create_partner_key(partner1_name, partner2_name):
    partners = [partner1_name, partner2_name]
    partners.sort()
    filtered_partners = list(filter(lambda x: x, partners))
    return '$'.join(filtered_partners)

def load_people(people_file):
    global next_person_id
    global next_partners_id

    with open(people_file, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for person_data in reader:
            person_data['ID'] = f'person{next_person_id}'
            next_person_id += 1

            person_data['Partners'] = set()
            person_data['Children'] = set()

            name = person_data['Birth Name']
            people[name] = person_data

            mother_name = person_data['Mother']
            father_name = person_data['Father']
            
            if mother_name or father_name:
                partner_key = create_partner_key(mother_name, father_name)
                if partner_key in partners:
                    partners[partner_key]['Found Child Count'] += 1
                else:
                    partners[partner_key] = {'ID': f'partners{next_partners_id}', 'Found Child Count': 1, 'Male': mother_name, 'Female': father_name}
                    next_partners_id += 1

    for person_date in people.values():
        name = person_data['Birth Name']
        mother_name = person_data['Mother']
        father_name = person_data['Father']

        if mother_name:
            people[mother_name]['Children'].add(name)
        
        if father_name:
            people[father_name]['Children'].add(name)

def load_marriages(marriages_file):
    global next_partners_id

    with open(marriages_file, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for marriage_data in reader:
            husband_name = marriage_data['Husband']
            wife_name = marriage_data['Wife']
            partner_key = create_partner_key(husband_name, wife_name)
            marriage_date = marriage_data['Date']
            marriage_location = marriage_data['Location']
            child_count = marriage_data['Child Count']
            if partner_key in partners:
                partners[partner_key]['Marriage Date'] = marriage_date
                partners[partner_key]['Marriage Location'] = marriage_location
                partners[partner_key]['Child Count'] = child_count
            else:
                partners[partner_key] = {'ID': f'partners{next_partners_id}', 'Found Child Count': 0, 'Child Count': child_count, 'Marriage Date': marriage_date, 'Marriage Location': marriage_location, 'Male': husband_name, 'Female': wife_name}
                next_partners_id += 1

    for partner_data in partners.values():
        male_name = partner_data['Male']
        female_name = partner_data['Female']
        if male_name and female_name:
            people[male_name]['Partners'].add(female_name)
            people[female_name]['Partners'].add(male_name)

def walk_graph(root_names, visitor_func):
    visited = set()
    to_visit = root_names.copy()
    while len(to_visit) > 0:
        person_name = to_visit.pop()
        person_data = people[person_name]

        mother_name = person_data['Mother']
        father_name = person_data['Father']
        
        if mother_name and not mother_name in visited:
            to_visit.append(mother_name)
        
        if father_name and not father_name in visited:
            to_visit.append(father_name)
        
        visitor_func(person_name)
        visited.add(person_name)

def highlight_visitor(person_name):
    person_data = people[person_name]

    mother_name = person_data['Mother']
    father_name = person_data['Father']
    
    if mother_name or father_name:
        partner_key = create_partner_key(mother_name, father_name)
        partner_data = partners[partner_key]
        partner_data['Highlight'] = True

    person_data['Highlight'] = True

def sort_people_names():
    names = list(people)
    for partner_data in partners.values():
        male_name = partner_data['Male']
        female_name = partner_data['Female']
        if male_name and female_name:
            male_index = names.index(male_name)
            female_index = names.index(female_name)
            if (female_index > male_index):
                names[male_index], names[female_index] = names[female_index], names[male_index]
    return names

def print_person_node(f, person_name):
    person_data = people[person_name]
    person_id = person_data['ID']
    birth_location = person_data['Birth Location']
    birth_year = person_data['Birth Date'].split("-")[0]
    death_year = person_data['Death Date'].split("-")[0]

    sanitized_name = person_name.replace('"', '\\"')
    label_parts = [sanitized_name]
    if birth_year or death_year:
        birth_year = birth_year or '?'
        label_parts.append(f'{birth_year}-{death_year}')

    if birth_location:
        label_parts.append(f'{birth_location}')

    color = 'black'
    font_color = 'black'
    if 'Highlight' in person_data:
        color = HIGHLIGHT_NODE_COLOR
        font_color = HIGHLIGHT_FONT_COLOR

    label = '\n'.join(label_parts)
    f.write(f'  {person_id} [shape=box,color={color},fontcolor={font_color},label="{label}"]\n')

def print_partner_node(f, partner_key):
    partner_data = partners[partner_key]
    partner_id = partner_data['ID']

    label_parts = []
    if 'Marriage Date' in partner_data:
        marriage_year = partner_data['Marriage Date'].split('-')[0]
        if marriage_year:
            label_parts.append(f'Married {marriage_year}')
        else:
            label_parts.append(f'Married')

    if 'Marriage Location' in partner_data:
        marriage_location = partner_data['Marriage Location']
        if marriage_location:
            label_parts.append(marriage_location)

    child_count = partner_data['Found Child Count']
    if 'Child Count' in partner_data and partner_data['Child Count'] != '':
        child_count = max(int(partner_data['Child Count']), child_count)
    
    if child_count == 0:
        label_parts.append('No children')
    elif child_count == 1:
        label_parts.append('1 child')
    else:
        label_parts.append(f'{child_count} children')

    color = 'black'
    font_color = 'black'
    if 'Highlight' in partner_data:
        color = HIGHLIGHT_NODE_COLOR
        font_color = HIGHLIGHT_FONT_COLOR

    label = '\n'.join(label_parts)
    f.write(f'  {partner_id} [shape=ellipse,color={color},fontcolor={font_color},label="{label}"]\n')

def print_person_edges(f, person_name):
    person_data = people[person_name]
    person_id = person_data['ID']
    name = person_data['Birth Name']
    mother_name = person_data['Mother']
    father_name = person_data['Father']

    if mother_name or father_name:
        partner_key = create_partner_key(mother_name, father_name)
        partner_data = partners[partner_key]
        partner_id = partner_data['ID']

        color = 'black'
        if 'Highlight' in partner_data and 'Highlight' in person_data:
            color = HIGHLIGHT_EDGE_COLOR

        f.write(f'  {partner_id} -> {person_id} [color={color},tailport=s,headport=n]\n')

    if name in partners:
        partner_data = partners[name]
        partner_id = partner_data['ID']

        color = 'black'
        if 'Highlight' in partner_data and 'Highlight' in person_data:
            color = HIGHLIGHT_EDGE_COLOR

        f.write(f'  {person_id} -> {partner_id} [color={color},tailport=s,headport=n]\n')
    
    for partner_name in person_data['Partners']:
        partner_key = create_partner_key(name, partner_name)
        partner_data = partners[partner_key]
        partner_id = partner_data['ID']

        color = 'black'
        if 'Highlight' in partner_data and 'Highlight' in person_data:
            color = HIGHLIGHT_EDGE_COLOR

        f.write(f'  {person_id} -> {partner_id} [color={color},tailport=s,headport=n]\n')

def print_graph(output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('digraph D {\n')
        f.write('ordering="in"\n')

        for person_name in sort_people_names():
            print_person_node(f, person_name)

        for partner_key in partners.keys():
            print_partner_node(f, partner_key)

        for person_name in people.keys():
            print_person_edges(f, person_name)

        f.write('}\n')

parser = argparse.ArgumentParser(description='Generate a family tree in Graphviz dot format.')
parser.add_argument('-p', '--people-file', required=True, help='path to input CSV file with people in family')
parser.add_argument('-m', '--marriages-file',  required=True, help='path to input CSV file with marriages in family')
parser.add_argument('-o', '--output', default='family-tree.dot', help='path to output dot file (default=family-tree.dot)')
parser.add_argument('--highlight', nargs='+', metavar='NAME', help='list of people to highlight ancestors of in tree')
args = parser.parse_args()

load_people(args.people_file)
load_marriages(args.marriages_file)

to_highlight = args.highlight.copy() if args.highlight else []
walk_graph(to_highlight, highlight_visitor)

print_graph(args.output)
