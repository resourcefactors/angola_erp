// Copyright (c) 2016, Helio de Jesus and contributors
// For license information, please see license.txt


//frappe.provide('frappe.pages');
//frappe.provide('frappe.views');
//frappe.provide("angola_erp.testes_grid");

//frappe.require("assets/angola_erp/js/lib/slickgrid_extended/slickgrid_extended.js");
//frappe.require("assets/angola_erp/js/lib/slickgrid_extended/plot_diagram.js");
//frappe.require("assets/angola_erp/js/lib/slickgrid_extended/slickgrid_extended.css");

//frappe.require("assets/angola_erp/js/lib/flot/jquery-ui.js");
//frappe.require("assets/angola_erp/js/lib/flot/jquery-ui.css");
//frappe.require("assets/angola_erp/js/lib/flot/jquery.flot.js");
//frappe.require("assets/angola_erp/js/lib/flot/jquery.flot.resize.js");
//frappe.require("assets/angola_erp/js/lib/flot/jquery.flot.crosshair.js");
//frappe.require("assets/angola_erp/js/lib/flot/jquery.flot.time.js");
//frappe.require("assets/angola_erp/js/lib/flot/jquery.contextmenu.js");


//frappe.require("assets/erp_customization/js/slick/lib/firebugx.js");
//frappe.require("assets/erp_customization/js/slick/plugins/slick.cellrangedecorator.js");
//frappe.require("assets/erp_customization/js/slick/plugins/slick.cellrangeselector.js");
//frappe.require("assets/erp_customization/js/slick/plugins/slick.cellselectionmodel.js");



//frappe.require("assets/erp_customization/js/slick/slick.formatters.js");
//frappe.require("assets/erp_customization/js/slick/slick.editors.js");
//frappe.require("assets/erp_customization/js/slick/slick.grid.js");
//frappe.require("assets/erp_customization/js/slick/slick.core.js");



//frappe.require("assets/erp_customization/js/slick/slick.groupitemmetadataprovider.js");
//frappe.require("assets/erp_customization/js/slick/slick.dataview.js");
//frappe.require("assets/erp_customization/js/slick/controls/slick.pager.js");
//frappe.require("assets/erp_customization/js/slick/controls/slick.columnpicker.js");

//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.checkboxselectcolumn.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.rowselectionmodel.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.autotooltips.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellcopymanager.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellexternalcopymanager.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.rowselectionmodel.js");



frappe.query_reports["TESTES_GRID"] = {
	"filters": [

	]

},
fff()

function fff() {

 var columns = [{ id: 'col0', name: 'Time',      toolTip: 'Date/Time',   sort_type: 'date' , plot_master_time: 'true' },
                   { id: 'col1', name: 'Value 1',   toolTip: 'Value 1',     sort_type: 'float',     style: 'text-align: right;'},
                   { id: 'col2', name: 'Value 2',   toolTip: 'Value 2',     sort_type: 'float',     style: 'text-align: right;'},
                   { id: 'col3', name: 'Value 3',   toolTip: 'Value 3',     sort_type: 'float',     style: 'text-align: right;'},
    ];                                                                                                                      
                                                                                                                            
    var options = { caption:            'Time line with diagram',                 
                    width:              '100%',                                                                             
                    maxHeight:          '100',                                                                              
                    locale:              'en',
    };                                                                                                                      
                                                                                                                            
    var data = [{ col0: '2013/10/01 14:05', col1: '66,20', col2: '12124', col3: '12' },
                { col0: '2013/10/01 14:10', col1: '22,10', col2: '23344', col3: '22' },
                { col0: '2013/10/01 14:20', col1: '33,40', col2: '65472', col3: '55' },
                { col0: '2013/10/01 14:30', col1: '77,90', col2: '81224', col3: '22' },
                { col0: '2013/10/01 14:40', col1: '10,20', col2: '12421', col3: '55' },
                { col0: '2013/10/01 14:50', col1: '12,24', col2: '23552', col3: '88' },
                { col0: '2013/10/01 15:00', col1: '88,20', col2: '36333', col3: '65' },
                { col0: '2013/10/01 15:20', col1: '45,30', col2: '23355', col3: '14' },
                { col0: '2013/10/01 15:40', col1: '55,40', col2: '23566', col3: '23' },
    ];                                                                                                                      
                                                                                                                            
    var additional_menu_entries = [{ label: 'Additional entry', hint: 'Additional entry just for fun', action: function(t){alert('Just for fun');} }];   

    $("<table width='100%>\
  <tr>\
    <td valign='top' width='50%'>\
      <div id='myGrid' style='width:100%;height:500px;''></div>\
    </td>\
  </tr>\
</table>").appendTo(frappe.container.page).find('.page-body');

                                                                                                                            
    createSlickGridExtended('myGrid', data, columns, options, additional_menu_entries);                         

};


function fffaaaaa() {
          
    var columns = [{ id: 'col0', name: 'Name, Vorname', toolTip: 'Name, Vorname der Person', sort_type: 'string' },
                   { id: 'col1', name: 'Gehalt',        toolTip: 'Gehalt der Person',        sort_type: 'float',     style: 'text-align: right;'},
                   { id: 'col2', name: 'Alter',         toolTip: 'Alter der Person',         sort_type: 'float',     style: 'text-align: right;'},
                   { id: 'col3', name: 'Geboren',       toolTip: 'Geburtsdatum der Person',  sort_type: 'date' },
    ];

    var options = { caption:            '<span style=\"font-weight: bold;\">Unlimited height and width</span>',
                    locale:              'en',
    };

    var data = [{ col0: 'Meier, Franz', col1: '4500,20', col2: '45', col3: '10.01.1962',
                  metadata: { columns: { col0: {title: 'Meier'}, col2: {title: 'Alter = 45'}
                                       },
                            },
                },
                { col0: 'Huber, Xaver', col1: '2500,18', col2: '55', col3: '19.02.1958',
                  metadata: { columns: { col0: {title: 'Huber'}, col2: {title: 'Alter = 55'}
                                       },
                            },
                },
                { col0: 'Beckenbauer, Heinrich', col1: '2500,18', col2: '61', col3: '14.11.1952',
                  metadata: { columns: { col0: {title: 'Beckenbauer'}, col2: {title: 'Alter = 61'}
                                       },
                            },
                }
    ];

//    var additional_menu_entries = [];

  
    $("<table width='100%>\
  <tr>\
    <td valign='top' width='50%'>\
      <div id='myGrid' style='width:100%;height:500px;''></div>\
    </td>\
  </tr>\
</table>").appendTo(frappe.container.page).find('.results');

	var dd1 = frappe.container.page;
	alert(dd1)
	var dd = document.getElementById('unique-0');
	alert(dd)
	dd.style.visibility ='hidden';

		var additional_menu_entries = [{ label: 'Additional entry', hint: 'Additional entry just for fun', action: function(t){alert('Just for fun');} }];
		//alert(typeof(data))
	createSlickGridExtended('myGrid', data, columns, options, additional_menu_entries);
//		createSlickGridExtended('myGrid', data, columns, options, additional_menu_entries);
//		grid = new Slick.Grid("#myGrid", data, columns, options);
	
};


