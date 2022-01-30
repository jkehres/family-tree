import csv
import argparse

HIGHLIGHT_FONT_COLOR = 'blue'
HIGHLIGHT_NODE_COLOR = 'blue'
HIGHLIGHT_EDGE_COLOR = 'blue'

parser = argparse.ArgumentParser(description='Generate a family tree in Graphviz dot format.')
parser.add_argument('-p', '--people-file', required=True, help='path to input CSV file with people in family')
parser.add_argument('-m', '--marriages-file',  required=True, help='path to input CSV file with marriages in family')
parser.add_argument('-o', '--output', default='family-tree.dot', help='path to output dot file (default=family-tree.dot)')
parser.add_argument('--highlight', nargs='+', metavar='NAME', help='list of people to highlight ancestors of in tree')
args = parser.parse_args()

def create_partner_key(partner1_name, partner2_name):
    partners = [partner1_name, partner2_name]
    partners.sort()
    filtered_partners = list(filter(lambda x: x, partners))
    return '$'.join(filtered_partners)

people = {}
partners = {}
next_person_id = 0
next_partners_id = 0

with open(args.people_file, encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    for person_data in reader:
        person_data['ID'] = f'person{next_person_id}'
        person_data['Partners'] = set()
        next_person_id += 1

        name = person_data['Birth Name']
        people[name] = person_data

        mother_name = person_data['Mother']
        father_name = person_data['Father']
        
        if mother_name or father_name:
            partner_key = create_partner_key(mother_name, father_name)
            if partner_key in partners:
                partners[partner_key]['Found Child Count'] += 1
            else:
                partners[partner_key] = {'ID': f'partners{next_partners_id}', 'Found Child Count': 1}
                next_partners_id += 1

with open(args.marriages_file, encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    for marriage_data in reader:
        partner_key = create_partner_key(marriage_data['Husband'], marriage_data['Wife'])
        marriage_date = marriage_data['Date']
        marriage_location = marriage_data['Location']
        child_count = marriage_data['Child Count']
        if partner_key in partners:
            partners[partner_key]['Marriage Date'] = marriage_date
            partners[partner_key]['Marriage Location'] = marriage_location
            partners[partner_key]['Child Count'] = child_count
        else:
            partners[partner_key] = {'ID': f'partners{next_partners_id}', 'Found Child Count': 0, 'Child Count': child_count, 'Marriage Date': marriage_date, 'Marriage Location': marriage_location}
            next_partners_id += 1

for partner_key in partners.keys():
    partner_names = partner_key.split('$')
    if len(partner_names) == 2:
        partner1_name, partner2_name = partner_names
        people[partner1_name]['Partners'].add(partner2_name)
        people[partner2_name]['Partners'].add(partner1_name)

visited = set()
to_visit = args.highlight.copy() if args.highlight else []
while len(to_visit) > 0:
    person_name = to_visit.pop()
    person_data = people[person_name]

    mother_name = person_data['Mother']
    father_name = person_data['Father']
    
    if mother_name and not mother_name in visited:
        to_visit.append(mother_name)
    
    if father_name and not father_name in visited:
        to_visit.append(father_name)
    
    if mother_name or father_name:
        partner_key = create_partner_key(mother_name, father_name)
        partner_data = partners[partner_key]
        partner_data['Highlight'] = True

    person_data['Highlight'] = True
    visited.add(person_name)

with open(args.output, 'w', encoding='utf-8') as f:
    f.write('digraph D {\n')

    for person_data in people.values():
        id = person_data['ID']
        name = person_data['Birth Name'].replace('"', '\\"')
        birth_location = person_data['Birth Location']
        birth_year = person_data['Birth Date'].split("-")[0]
        death_year = person_data['Death Date'].split("-")[0]

        label_parts = [name]
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
        f.write(f'  {id} [shape=box,color={color},fontcolor={font_color},label="{label}"]\n')

    for partner_data in partners.values():
        id = partner_data['ID']

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
        f.write(f'  {id} [shape=ellipse,color={color},fontcolor={font_color},label="{label}"]\n')

    for person_data in people.values():
        id = person_data['ID']
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

            f.write(f'  {partner_id} -> {id} [color={color},tailport=s,headport=n]\n')

        if name in partners:
            partner_data = partners[name]
            partner_id = partner_data['ID']

            color = 'black'
            if 'Highlight' in partner_data and 'Highlight' in person_data:
                color = HIGHLIGHT_EDGE_COLOR

            f.write(f'  {id} -> {partner_id} [color={color},tailport=s,headport=n]\n')
        
        for partner_name in person_data['Partners']:
            partner_key = create_partner_key(name, partner_name)
            partner_data = partners[partner_key]
            partner_id = partner_data['ID']

            color = 'black'
            if 'Highlight' in partner_data and 'Highlight' in person_data:
                color = HIGHLIGHT_EDGE_COLOR

            f.write(f'  {id} -> {partner_id} [color={color},tailport=s,headport=n]\n')

    f.write('}\n')
