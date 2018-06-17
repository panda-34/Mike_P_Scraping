import csv, json

csv.field_size_limit(1024*1024)

def main():
	enc = json.JSONEncoder(check_circular=False, separators=(',', ':'))
	#enc = json.JSONEncoder(check_circular=False, indent=2)
	with open('seekingalpha.csv', newline='', encoding='utf_8_sig') as f_in, open('seekingalpha.json', 'w') as f_j, open('header.csv', 'w', newline='', encoding='utf_8_sig') as f_h:
		reader = csv.DictReader(f_in)
		fields = reader.fieldnames.copy()
		fields.remove('Text')
		writer = csv.DictWriter(f_h, fields)
		writer.writeheader()
		f_j.write('[')
		for i, row in enumerate(reader):
			if i > 0:
				f_j.write(',')
			f_j.write(enc.encode(row))
			del row['Text']
			writer.writerow(row)
		f_j.write(']')

if __name__ == '__main__':
	main()
