import scrapy
import pandas as pd
import os
import os.path

class PokemonScrapper(scrapy.Spider):
  name = 'pokemon_scrapper'
  domain = "https://pokemondb.net/"
  start_urls = ["https://pokemondb.net/pokedex/all"]

  def parse(self, response):
    csv = os.path.isfile("file.csv")
    if not csv:
      pokemons = response.css('#pokedex > tbody > tr')
      for pokemon in pokemons:
        link = pokemon.css("td.cell-name > a::attr(href)").extract_first()
        yield response.follow(self.domain + link, self.parse_pokemon)

  def parse_pokemon(self, response):
    pokedex_types = []
    tables = response.css('.vitals-table')
    
    for table in tables:
      header = table.css('tr:nth-child(2) th::text').get()
      if header and 'Type' in header:
        #Capturar os tipos se a tabela for a correta
        types = table.css('tr:nth-child(2) > td > a')
        for type_element in types:
          pokedex_types.append(type_element.css('::text').get())
        break

    abilities_names = []
    abilities_descs = []
    abilities_urls = []
    abilities_elements = response.css('.vitals-table > tbody > tr:nth-child(6) > td span.text-muted, .vitals-table > tbody > tr:nth-child(6) > td small.text-muted')
    #Capturar múltiplas habilidades
    for element in abilities_elements:
      abilitie_name = element.css('a::text').get()
      abilitie_desc = element.css('a::attr(title)').get()
      abilitie_relative_url = element.css('a::attr(href)').get()
      abilitie_url = self.domain + abilitie_relative_url if abilitie_relative_url else None
      abilities_names.append(abilitie_name)
      abilities_descs.append(f" {abilitie_desc}")
      abilities_urls.append(f" {abilitie_url}")


    evolutions_names = []
    evolutions_numbers = []
    evolutions_urls = []
    evolution_elements = response.css('#main > div.infocard-list-evo > div > span.infocard-lg-data.text-muted')
    eevee_evolutions_name = ['Vaporeon', 'Jolteon', 'Flareon', 'Espeon', 'Umbreon', 'Leafeon', 'Glaceon', 'Sylveon']
    #Capturar múltiplas evoluções
    i = 1
    for element in evolution_elements[1:]:
      evolution_name = element.css('a.ent-name::text').get()
      if evolution_name == "Eevee": #Ajustar o selector caso seja Eevee
        i += 1
        if i == 3:
          eevee_evolutions = response.css('#main > div.infocard-list-evo > span.infocard-evo-split > div.infocard-list-evo > div > span.infocard-lg-data.text-muted')
          for eevee_evolution in eevee_evolutions:
            evolution_name = eevee_evolution.css('a.ent-name::text').get()
            evolution_relative_link = eevee_evolution.css('a.ent-name::attr(href)').get()
            evolution_number = eevee_evolution.css('small::text').get()
            evolution_url = self.domain + evolution_relative_link if evolution_relative_link else None
            evolutions_names.append(evolution_name)
            evolutions_numbers.append(f" {evolution_number}")
            evolutions_urls.append(f" {evolution_url}")
      else:
        evolution_relative_link = element.css('a.ent-name::attr(href)').get()
        evolution_number = element.css('small::text').get()
        evolution_url = self.domain + evolution_relative_link if evolution_relative_link else None
        evolutions_names.append(evolution_name)
        evolutions_numbers.append(f" {evolution_number}")
        evolutions_urls.append(f" {evolution_url}")


    pokemon_name = response.css('#main > h1::text').get()
    
    #Tratamento dos Dados
    #Verificar se o pokemon é o ultimo da lista de evolução ou faz parte da evolução do Eevee
    #Apagar a lista de evolução
    if (evolutions_names and pokemon_name == evolutions_names[-1]) or (evolutions_names and pokemon_name in eevee_evolutions_name):
      evolutions_names.clear()
      evolutions_numbers.clear()
      evolutions_urls.clear()
      
    #Verificar se o pokemon é uma evolução, porém não é a ultima evolução
    #Apagar as evoluções anteriores
    if evolutions_names and pokemon_name != evolutions_names[-1] and pokemon_name in evolutions_names:
      index = evolutions_names.index(pokemon_name)
      for num in range(index + 1):
        del evolutions_names[0]
        del evolutions_numbers[0]

    yield {
      'Nome': response.css('#main > h1::text').get(),
      'Número': response.css('.vitals-table > tbody > tr:nth-child(1) > td > strong::text').get(),
      'Peso': response.css('.vitals-table > tbody > tr:nth-child(5) > td::text').get(),
      'Altura': response.css('.vitals-table > tbody > tr:nth-child(4) > td::text').get(),
      'Tipos': pokedex_types,
      'Habilidades': abilities_names,
      'Habilidades Descrição': abilities_descs,
      'Habilidades URL': abilities_urls,
      'Url Pokémon': response.css('head > link[rel="canonical"]::attr(href)').get(),
      'Evoluções': evolutions_names,
      'Evoluções Número': evolutions_numbers,
      'Evoluções URL': evolutions_urls}


os.system('clear')
csv = os.path.isfile("file.csv")
if csv:
  pd.set_option('display.max_columns', None)
  pd.set_option('display.width', None)
  pd.set_option('display.max_colwidth', None)

  pokemons = pd.read_csv('file.csv')

  #Tratamento de Dados
  pokemons['Evoluções'] = pokemons['Evoluções'].str.replace(r"[\[\]\{\}\']", '', regex=True)
  pokemons['Habilidades'] = pokemons['Habilidades'].str.replace(r"[\[\]\{\}\']", '', regex=True)
  pokemons['Peso'] = pokemons['Peso'].str.replace(r'\s*\(.*?\)', '', regex=True)
  pokemons['Altura'] = pokemons['Altura'].str.replace(r'\s*\(.*?\)', '', regex=True)
  pokemons['Altura'] = pokemons['Altura'].str.replace('m', '').astype(float)
  pokemons['Altura'] = pokemons['Altura'] * 100
  pokemons['Altura'] = pokemons['Altura'].astype(str) + ' cm'

  #Demonstração do tratamento de dados quando é evolução, porém não é a ultima
  #Deverá remover as evoluções anteriores e a atual
  print("Demonstração: Pokémon Evoluído e Possui Mais Evoluções")
  ivysaur_index = pokemons[pokemons['Nome'] == 'Ivysaur'].index[0]
  ivysaur = pokemons.iloc[ivysaur_index]
  print(ivysaur)
  print("\n\n")

  #Demonstração do tratamento de dados quando é a ultima evolução
  #Deverá remover todas as evoluções
  print("Demonstração: Pokémon Última Evolução")
  venusaur_index = pokemons[pokemons['Nome'] == 'Venusaur'].index[0]
  venusaur = pokemons.iloc[venusaur_index]
  print(venusaur)
  print("\n\n")
  
  #Demonstração do tratamento de dados para caso Eevee
  print("Demonstração: Evoluções Eevee")
  eevee_index = pokemons[pokemons['Nome'] == 'Eevee'].index[0]
  eevee = pokemons.iloc[eevee_index]
  print(eevee)
  print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")      