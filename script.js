const c = document.getElementById('table');
var res, hot, exportPlugin

const header = [
  ["IOC_sort","IOC 10.1 sequence. Unique number per sub/species. "],
["Rank","Species or Subspecies"],
["Order",""],
["Family",""],
["Scientific Name","Latin name (2 words for species, 3 for subspecies)"],
["Common Name","English name"],
["Clements--Sort","Sort key of Clements taxonomy"],
["Clements--code","Specie code of eBird/Clements"],
["Clements--Scientific Name",""],
["Clements--Common Name",""],
["Clements--Family",""],
["Clements--range","Description of the distribution range "],
["H&M--Scientific Name",""],
["H&M--Common Name",""],
["H&M--sort_key",""],
["H&M--range",""],
["HBW-BL--Scientific Name",""],
["HBW-BL--Common Name",""],
["HBW-BL--Note",""],
["HBW-BL--SISRecID",""],
["Status Birdlife",""],
["2019 IUCN Red List category",""],
["IOC--Breeding Range","Description of the distribution range "],
["IOC--Nonbreeding Range","Description of the distribution range "],
["IOC--Code","*unknow meaning*"],
["IOC--Note",""],
["96#","Sorting key according to the 96 checklist"],
["2009#","Sorting key according to the 2009 checklist"],
["2019#","Sorting key according to the 2019 checklist"],
["ADU","Reference number given by the Animal Demography Unit (ADU) (http://www.adu.uct.ac.za/)"],
["AM","Afrotropical migrant"],
["AMR","Afrotropical migrant and resident. Enteterd as 'am' or '(am)'"],
["E","endemic species or race"],
["EX","species which are thought to have become extinct in Kenya"],
["HIST","no record for 50 years, i.e. no record since 1968 or earlier. Entered as 'Hist.'"],
["IO","visitor from northwest Indian Ocean islands"],
["MM","migrant from the Malagasy region"],
["N","nomadic/wanderer"],
["NR","nomadic/wanderer and resident. Entered as (n)"],
["NRR","not recently recorded, i.e. since the period 1969 to 1999"],
["OM","migrant from the Oriental region"],
["PM","migrant from the Palaearctic region"],
["PMR","migrant from the Palaearctic region and resident. Entered as 'pm' or '(pm)'"],
["RAR","Fewer than 5 records on East African Rarities Committee list at time of publication. Entered as 'Rar.'"],
["RS","visitor from the Red Sea"],
["SO","visitor from the Southern Ocean or Antarctica"],
["VIO","vagrant* from the northwest Indian Ocean"],
["VM","vagrant* from the Malagasy region "],
["VN","vagrant* from the Nearctic region"],
["VO","vagrant* from the Oriental region"],
["VP","vagrant from the Palaearctic region"],
["VSO","vagrant* from the Southern Ocean or Antarctica"],
["VSA","vagrant* from southern Africa"],
["Note 2019","Note of the 2019 Checklist including reference"],
["Note 2009","Note of the 2009 checklist including reference"]
];


Papa.parse("main.csv", {
  encoding: "UTF-8",
  download: true,
  complete: function(results) {
    res = results
    console.log("Finished" );
    hot = new Handsontable(c, {
      data: results.data.slice(1),
      colHeaders: results.data[0],
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
        if(width > 300){
          return 300
        }
      },
      hiddenColumns: {
        columns: [6],
        indicators: true
      },
      contextMenu: ['freeze_column', 'unfreeze_column','---------','hidden_columns_hide','hidden_columns_show','---------','filter_by_value','filter_action_bar'],
      afterGetColHeader: function(col, TH){
        var header_filter = header.filter(e=>e[0]==TH.innerText)[0]
        if (header_filter === undefined || header_filter.length == 0) {
          TH.innerHTML = TH.innerText
        } else {
          TH.innerHTML = '<div title="' + header_filter[1] + '">' + TH.innerText + '</div>'
        }
        //TH.innerHTML = col
      }
    });
    const filtersPlugin = hot.getPlugin('filters');
    filtersPlugin.addCondition(3, 'eq', ['Species']);
    filtersPlugin.filter();
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
