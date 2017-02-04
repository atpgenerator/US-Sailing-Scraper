import requests as r
import pandas as pd
from pattern.web import Element
from pattern.web import plaintext
import os

# base_url = "http://scores.collegesailing.org/"

class SailingScraper:
	total_data = 0

	# highest level scraper, sets up tree structure for files and finds seasons
	def scrapeSite(self):
		url = "http://scores.collegesailing.org/seasons/"
		base_url = "http://scores.collegesailing.org"
		os.makedirs(os.getcwd() + "/sailing_data")
		elements = Element(r.get(url).content)("div#content-header ul#page-info li")
		for elm in elements:
			name = elm("span.page-info-key")[0].content
			print name
			link = base_url + elm("span.page-info-value a")[0].attr['href']
			self.scrapeSeason(link, os.getcwd() + "/sailing_data", name)

	# goes thorugh a season, finding the regattas and passing the info to scrapeRegatta
	def scrapeSeason(self, url, path, season):
		path = path + "/" + season + "/"
		os.makedirs(path)
		season_content = r.get(url).content
		e = Element(season_content)
		regatta_links = [elm for elm in e("div#page-content div.port table.season-summary td a")]
		for link in regatta_links:
			temp_url = url + link.attr['href'] + "/"
			self.scrapeRegatta(temp_url, path)
			print self.total_data

	# Gets all the divisions in a regatta and gathers their data
	# if the regatta has no dvisions it just gets the total
	def scrapeRegatta(self, url, path):
		name = self.getName(url)
		print "  ", name
		divisions = self.getDivisions(url)
		if divisions:
			for d in divisions:
				self.scrapeDivision(url, d).to_csv(path + name + "-" + d[0] + ".csv" , encoding='utf-8')
		else:
			regatta_df = self.scrapeNoDivision(url)
			if type(regatta_df) != type(pd.DataFrame()):
				print "ERROR: " + name
				# fail case for one type of page that has yet to be handeled
			else:
				regatta_df.to_csv(path + name + ".csv" , encoding='utf-8')

	# goes through the divisions of a regatta and gathers the speicifc data
	def scrapeDivision(self, url, division):
		url += division
		division = division[0]
		# print "   Div: ", division
		data = {'Team': [],
				'Total Score': [],
				'Skipper': [],
				'Placement': [], 
				'Division': [] }
		e = Element(r.get(url).content)
		for row in e("table.results tr.topborder"):
			data['Team'].append(plaintext(row("td.schoolname")[0].content))
			# print "      Team:", data['Team'][-1]
			data['Total Score'].append(plaintext(row("td.totalcell")[0].content))
			try: 
				data['Skipper'].append(plaintext(row("td.skipper")[0].content))
			except:
				data['Skipper'].append("none")
			data['Placement'].append(plaintext(row("td")[1].content))
			data['Division'].append(division)


		if len(data['Total Score']) != len(data['Skipper']) or len(data['Placement']) != len(data['Team']) or len(data['Division']) != len(data['Total Score']):
			return None
		self.total_data += 5 * len(data['Total Score'])
		return pd.DataFrame.from_dict(data).set_index(["Division", "Placement"])

	# gets the total scores from a regatta
	def scrapeNoDivision(self, url):
		data = {}
		e = Element(r.get(url).content)
		data['Team'] = [plaintext(elm.content) for elm in e("tr td.schoolname a")]
		data['Total Score'] = [plaintext(elm.content) for elm in e("td.totalcell")]
		data['Skipper'] = [plaintext(elm.content) for elm in e("td.teamname")]
		data['Placement'] = [i for i in range(1, len(data['Team'])+1 )]
		data['Division'] = ['A' for i in range(len(data['Team']))]

		if len(data['Total Score']) != len(data['Skipper']) or len(data['Placement']) != len(data['Team']) or len(data['Division']) != len(data['Total Score']):
			return None
		self.total_data += 5 * len(data['Total Score'])
		return pd.DataFrame.from_dict(data).set_index(["Division", "Placement"])


	# Helper functions to help clean the code above
	def getName(self, url):
		name = Element(r.get(url).content)("div#content-header h1 span")[1].content
		name = plaintext(name)
		while "/" in name:
			name = name.replace("/", "-")
		return name

	def getDivisions(self, url):
		divisions = ["A/", "B/", "C/", "D/", "E/"]
		fin = []
		for d in divisions:
			temp_url = url + d
			if r.get(temp_url).status_code == 200:
				fin.append(d)
		return fin


s = SailingScraper()
s.scrapeSite()