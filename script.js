const c = document.getElementById('table');
var res, hot, exportPlugin

var header = [
  ['sort', 'Sorting key (according to the 2019 checklist)'],
  ['family_scientific', 'Family (https://en.wikipedia.org/wiki/Family_(biology))'],
  ['family_english', 'Family in common name'],
  ['common_name', 'Common Name'],
  ['scientific_name', 'Scientific Name'],
  ['AM', 'Afrotropical migrant'],
  ['AMR', 'Afrotropical migrant and resident. Enteterd as "am" or "(am")'],
  ['E', 'endemic species or race'],
  ['EX', 'species which are thought to have become extinct in Kenya'],
  ['HIST', 'no record for 50 years, i.e. no record since 1968 or earlier. Entered as "Hist."'],
  ['IO', 'visitor from northwest Indian Ocean islands'],
  ['MM', 'migrant from the Malagasy region'],
  ['N', 'nomadic/wanderer'],
  ['NR', 'nomadic/wanderer and resident. Entered as (n)'],
  ['NRR', 'not recently recorded, i.e. since the period 1969 to 1999'],
  ['OM', 'migrant from the Oriental region'],
  ['PM', 'migrant from the Palaearctic region'],
  ['PMR', 'migrant from the Palaearctic region and resident. Entered as "pm" or "(pm)"'],
  ['RAR', 'Fewer than 5 records on East African Rarities Committee list at time of publication. Entered as "Rar."'],
  ['RS', 'visitor from the Red Sea'],
  ['SO', 'visitor from the Southern Ocean or Antarctica'],
  ['VIO', 'vagrant* from the northwest Indian Ocean'],
  ['VM', 'vagrant* from the Malagasy region '],
  ['VN', 'vagrant* from the Nearctic region'],
  ['VO', 'vagrant* from the Oriental region'],
  ['VP', 'vagrant from the Palaearctic region'],
  ['VSO', 'vagrant* from the Southern Ocean or Antarctica'],
  ['VSA', 'vagrant* from southern Africa'],
  ['comments', 'Any comments or reference in the 2019 checklist'],
  ['red_list', 'IUCN red list status (https://en.wikipedia.org/wiki/IUCN_Red_List): Least Concern, Vulnerable, Near Threatened, Endangered, Critically Endangered, Not Recognized, Data Deficient'],
  ['status_birdlife', 'Endemic, Introduced, Rare/Accidental'],
  ['water_bird', 'Is it a water bird according to International Wetland (see page 3 of https://europe.wetlands.org/wp-content/uploads/sites/3/2016/08/Protocol_for_waterbird_counting_En_.pdf)'],
  ['strict_water_bird', 'Is it a strict water bird (excluding some species not recorded during waterbirdcount)'],
  ['sort_1996', 'Sorting key according to the 1996 checklist'],
  ['sort_2009', 'Sorting key according to the 2009 checklist'],
  ['ADU', 'Identifier given by Animal Demographic Unit (http://www.adu.uct.ac.za/) and used on various projects including: CWAC, Kenyabirdnet, Safring…'],
  ['avibaseid', 'Identifier given by Avibase (http://avibase.bsc-eoc.org/)'],
  ['wikiDataID', 'Identifier given by Wikidata (https://www.wikidata.org/wiki/Wikidata:Identifiers)'],
  ['iNaturalisttaxonID', 'Identifier given by inaturalist (https://www.inaturalist.org/)'],
  ['ITIS', 'Identifier given by the Integrated Taxonomic Information System (https://www.itis.gov/)'],
  ['IUCNtaxonID', 'Identifier given by IUCN'],
  ['ARKiveID', 'Identifier given by ARKive'],
  ['ObservationorgID', 'Identifier given by observation.org (https://observation.org/)'],
  ['GBIFID', 'Identifier for GBIF'],
  ['IOC--sort', 'IOC sort key'],
  ['IOC--rank', 'IOC rank (species or subspecies)'],
  ['IOC--scientific_name', ''],
  ['IOC--common_name', ''],
  ['Clements--sort', ''],
  ['Clements--code', ''],
  ['Clements--rank', 'eBird/Clement rank includes Spuh, Slash, ISSF etc… (see https://ebird.org/science/the-ebird-taxonomy)'],
  ['Clements--scientific_name', ''],
  ['Clements--common_name', ''],
  ['H&M--sort', ''],
  ['H&M--rank', ''],
  ['H&M--scientific_name', ''],
  ['H&M--common_name', ''],
  ['HBW&BL--SISRecID', ''],
  ['HBW&BL--rank', ''],
  ['HBW&BL--scientific_name', ''],
  ['HBW&BL--common_name', ''],
  ['HBW&BL--note', ''],
  ['IOC--note', ''],
  ['IOC--breeding_range', ''],
  ['IOC--nonbreeding_range', ''],
  ['Clements--range', ''],
  ['H&M--range', ''],
  ['entry_checklist_of_kenya', 'Original name given in the 2019 checklist'],
  ['Note 2009', 'Notes and reference of the 2019 checklist']
  ];

header.push(['status','Different code to describe the species status'])

var d
Papa.parse("main.csv", {
  encoding: "UTF-8",
  download: true,
  complete: function(results) {
    d = results.data
    var h = d[0];
    var b = d.slice(1).map(e => {
      var dd={}
      e.forEach( (ee,i) => {
        if (h[i]=='avibaseid'){
          dd[h[i]] = '<a target="_blank" title="Avibase" href="https://avibase.bsc-eoc.org/species.jsp?avibaseid='+ee+'">'+ee+'</a>'
        } else if (h[i]=='HBW&BL--SISRecID'){
          dd[h[i]] = '<a target="_blank" title="Birdlife Factsheet" href="http://datazone.birdlife.org/species/factsheet/'+ee+'">'+ee+'</a>'
        } else if (h[i]=='Clements--code'){
          dd[h[i]] = '<a target="_blank" title="eBird Specie page" href="https://ebird.org/species/'+ee+'/KE">'+ee+'</a>'
        } else if (h[i]=='GBIFID'){
          dd[h[i]] = '<a target="_blank" title="GBIF" href="https://www.gbif.org/species/'+ee+'">'+ee+'</a>'
        } else if (h[i]=='iNaturalisttaxonID'){
          dd[h[i]] = '<a target="_blank" title="Observation in Kenya in inaturalist" href="https://www.inaturalist.org/observations?place_id=7042&taxon_id='+ee+'">'+ee+'</a>'
        } else if (h[i]=='ITIS'){
          dd[h[i]] = '<a target="_blank" title="ITIS" href="https://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value='+ee+'">'+ee+'</a>'
        } else if (h[i]=='IUCNtaxonID'){
          dd[h[i]] = '<a target="_blank" title="IUCN page" href="https://apiv3.iucnredlist.org/api/v3/taxonredirect/'+ee+'">'+ee+'</a>'
        } else if (h[i]=='wikiDataID'){
          dd[h[i]] = '<a target="_blank" title="wikidata" href="https://www.wikidata.org/wiki/'+ee+'">'+ee+'</a>'
        }  else if (h[i]=='ADU'){
          dd[h[i]] = '<a target="_blank" title="Kenya Bird Map Atlas" href="http://kenyabirdmap.adu.org.za/species_info.php?spp='+ee+'">'+ee+'</a>'
        } else if (h[i]=='ObservationorgID'){
          dd[h[i]] = '<a target="_blank" title="observado" href="https://observation.org/species/'+ee+'">'+ee+'</a>'
        } else if (h[i]=='red_list'){
          if (ee){
            dd[h[i]] = '<span title="'+ee+'">' +ee.match(/\b(\w)/g).join('') +'</span>'
          }
        } else {
          dd[h[i]] = ee
        }
      })
      return dd
    })

    const tocombine = ['AM', 'AMR', 'E', 'EX', 'HIST', 'IO', 'MM', 'N', 'NR', 'NRR', 'OM', 'PM', 'PMR', 'RAR', 'RS', 'SO', 'VIO', 'VM', 'VN', 'VO', 'VP', 'VSO', 'VSA']
    b = b.map(v => { 
      var combined = "";
      tocombine.forEach(c2=>{

        var h2 = header.find(element => element[0] == c2);
        if (v[c2]){
          combined += '<span title="'+h2[1]+'">'+h2[0]+'</span>, '
        }
        delete v[c2]
      })
      v['status'] = combined
      return v
    });
    var i = h.indexOf(tocombine[0])
    h=h.filter( hh => {
      return !tocombine.includes(hh)
    })
    h.splice(i, 0, "status");
    var col = h.map(hh => {
        return {
          data: hh,
          renderer: 'html'
        }
    })

    hidcol = ['water_bird','strict_water_bird','status_birdlife','family_scientific','family_english']
    hcol = hidcol.map(e=> h.indexOf(e))

    console.log("Load file finished" );
    hot = new Handsontable(c, {
      data: b,
      colHeaders: h,
      columns: col,
      multiColumnSorting: true,
      dropdownMenu: true,
      filters: true,
      readOnly: true,
      manualColumnResize: true,
      manualColumnFreeze: true,
      dropdownMenu: ['filter_by_condition', 'filter_by_value','filter_action_bar'],
      //width: '100%',
      //height: '100%',
      licenseKey: 'non-commercial-and-evaluation',
      contextMenu: true,
      modifyColWidth: function(width, col){
        if (width > 300){
          return 300
        }
      },
      hiddenColumns: {
        columns: hcol,
        indicators: true
      },
      contextMenu: ['freeze_column', 'unfreeze_column','---------','hidden_columns_hide','hidden_columns_show','---------','filter_by_value','filter_action_bar'],
      afterGetColHeader: function(col, TH){
        var header_filter = header.filter(e=>e[0]==TH.innerText)[0]
        if (header_filter === undefined || header_filter.length == 0) {
          TH.getElementsByClassName('colHeader')[0].innerHTML = TH.innerText
        } else {
          TH.getElementsByClassName('colHeader')[0].innerHTML = '<div title="' + header_filter[1] + '">' + TH.innerText + '</div>'
        }
      }
    });
    /*const filtersPlugin = hot.getPlugin('filters');
    filtersPlugin.addCondition(3, 'eq', ['Species']);
    filtersPlugin.filter();*/
    exportPlugin = hot.getPlugin('exportFile');
    
    var elem = document.getElementById("loader");
    elem.parentNode.removeChild(elem);   
    
  }
})
document.addEventListener('DOMContentLoaded', (event) => {
  
  var button1 = document.getElementById('exportFile');
  button1.addEventListener('click', function() {
    exportPlugin.downloadFile('csv', {
      //bom: false,
      columnDelimiter: ',',
      //columnHeaders: false,
      exportHiddenColumns: false,
      exportHiddenRows: false,
      fileExtension: 'csv',
      filename: 'Birds_of_Kenya_2019',
      mimeType: 'text/csv',
      rowDelimiter: '\r\n',
      //rowHeaders: true
    });
  });
})
