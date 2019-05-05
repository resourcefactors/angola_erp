frappe.pages["saft-ao"].on_page_load = function (wrapper) {
	frappe.saft_ao = new frappe.Saft_ao(wrapper);
}

frappe.Saft_ao = Class.extend({

	init: function (parent) {
		frappe.ui.make_app_page({
			parent: parent,
			title: "Gerar e Descarregar o SAFT-AO",
			single_column: false
		});

		this.parent = parent;
		this.page = this.parent.page;
		this.page.sidebar.html(`<ul class="module-sidebar-nav overlay-sidebar nav nav-pills nav-stacked"></ul>`);
		this.$sidebar_list = this.page.sidebar.find('ul');

		// const list of doctypes
		//this.doctypes = ["Sales Invoice", "Item", "Supplier", "Sales Partner","Sales Person"];
		this.doctypes = ["SAFT-AO"];
		this.timespans = ["Diario", "Semana", "Mensal", "Ano"];
		this.filters = {
			"SAFT-AO": ["0"],
		};
		this.tipoficheiro = ["I - Contabilidade Integrada","C - Contabilidade","F - Facturação","R - Recibos","S - Autofacturação","A - Aquisição de Bens e Serviços","Q - Aquisição de Bens e Serviços Integrada"];

		// for saving current selected filters
		// TODO: revert to 0 index for doctype and timespan, and remove preset down
		const _initial_doctype = this.doctypes[0];
		const _initial_timespan = this.timespans[0];
		const _initial_filter = this.filters[_initial_doctype];
		const _initial_tipoficheiro = this.tipoficheiro[0];

		this.options = {
			selected_doctype: _initial_doctype,
			selected_timespan: _initial_timespan,
			selected_tipoficheiro: _initial_tipoficheiro,
		};

		this.message = null;
		this.make();
	},

	make: function () {
		var me = this;

		var $container = $(`<div class="leaderboard page-main-content">
			<div class="leaderboard-graph"></div>
			<div class="leaderboard-list"></div>
		</div>`).appendTo(this.page.main);

		//this.$graph_area = $container.find('.leaderboard-graph');

		this.doctypes.map(doctype => {
			this.get_sidebar_item(doctype).appendTo(this.$sidebar_list);
		});

		this.company_select = this.page.add_field({
			fieldname: 'company',
			label: __('Company'),
			fieldtype:'Link',
			options:'Company',
			default:frappe.defaults.get_default('company'),
			reqd: 1,
			change: function() {
				me.options.selected_company = this.value;
				//me.make_request($container);
			}
		});
		this.timespan_select = this.page.add_select(__("Timespan"),
			this.timespans.map(d => {
				return {"label": __(d), value: d }
			})
		);

		this.dateinit_select = this.page.add_field({
			fieldname:'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.get_today()
			//width: '80'
		});
		this.tipoficheiro_select = this.page.add_select(__("Tipo de Ficheiro"),
			this.tipoficheiro.map(d => {
				return {"label": __(d), value: d }
			})
		);


		this.download_file_select = this.page.add_field({
			fieldname:"download_file",
			label: __("Download o Ficheiro"),
			fieldtype: "Button",


		});


		console.log('botao')

		$(this.download_file_select.$input).click( function() {
			//frappe.show_alert('msgprint', 'Iniciando processamento SAFT-AO...',3)
			frappe.msgprint("SAF-T(AO)","Iniciando processamento SAFT-AO...")
			console.log("Chama gerar saft...")
			frappe.call({
				method: "angola_erp.util.saft_ao.set_saft_ao",
				//method: "angola_erp.util.cambios.set_saft_ao",
				freeze: true,
				args: {
					"company": me.options.selected_company,
					"processar": me.options.selected_timespan,
					"datainicio": me.dateinit_select.value,
					"datafim": me.dateinit_select.value,
					"update_acc_codes": 1,
					"download_file": 1,
					"ficheiro_tipo": me.options.selected_tipoficheiro,
					"usuario": frappe.session.user,
				},
				async: false,
				/*
				callback: function (r) {

					let results = r.message || [];
					console.log('RESUTADOS.....')
					console.log(results.substring(results.search('/files/')))
					file = results.substring(results.search('/files/'))
					//console.log(frappe.utils.get_url(frappe.utils.cstr(frappe.local.site)))

					if (results) {
						//frm.add_custom_button("Link", function(){
						//	my_button.onclick=window.open('https://erpnext.com')
						//});


						//var client = new XMLHttpRequest();
						//client.onload = handler;
						//client.open("GET", results.substring(results.search('/files/')));
						//client.send();
						
						return window.open(results.substring(results.search('/files/')) ); 

						//return window.open(results.substring(results.search('/files/')) ); 
						//default to files/xxxx
						//var link = document.createElement("Ficheiro");
						//$ficheiro_select.download = results.substring(results.search('/files/'));
						//$ficheiro_select.href = "http://192.168.73.164:8000" // frappe.utils.get_url(frappe.utils.cstr(frappe.local.site));
						//$ficheiro_select.click();


					}
				}
				*/
			});
			

		});

		//this.type_select = this.page.add_select(__("Type"),
		//	me.options.selected_filter.map(d => {
		//		return {"label": __(frappe.model.unscrub(d)), value: d }
		//	})
		//);

		this.$sidebar_list.on('click', 'li', function(e) {
			let $li = $(this);
			let doctype = $li.find('span').attr("doctype-value");

			me.options.selected_company = frappe.defaults.get_default('company');
			me.options.selected_doctype = doctype;
			me.options.selected_filter = me.filters[doctype];
			me.options.selected_filter_item = me.filters[doctype][0];

			//me.type_select.empty().add_options(
			//	me.options.selected_filter.map(d => {
			//		return {"label": __(frappe.model.unscrub(d)), value: d }
			//	})
			//);

			me.$sidebar_list.find('li').removeClass('active');
			$li.addClass('active');

			//me.make_request($container);
		});

		this.timespan_select.on("change", function() {
			me.options.selected_timespan = this.value;
			//me.make_request($container);
		});

		this.tipoficheiro_select.on("change", function() {
			me.options.selected_tipoficheiro = this.value;
			//me.make_request($container);
		});

		//this.type_select.on("change", function() {
		//	me.options.selected_filter_item = this.value
			//me.make_request($container);
		//});

		// now get leaderboard
		this.$sidebar_list.find('li:first').trigger('click');
	},

	//make_request: function ($container) {
	//	var me = this;

	//	frappe.model.with_doctype(me.options.selected_doctype, function () {
	//		me.get_leaderboard(me.get_leaderboard_data, $container);
	//	});
	//},

	/*
	get_leaderboard: function (notify, $container) {
		var me = this;
		if(!me.options.selected_company) {
			frappe.throw(__("Please select Company"));
		}
		frappe.call({
			method: "angola_erp.angola_erpnext.page.saft_ao.saft_ao.get_saft_ao",
			args: {
				doctype: me.options.selected_doctype,
				timespan: me.options.selected_timespan,
				company: me.options.selected_company,
				field: me.options.selected_filter_item,
			},
			callback: function (r) {
				let results = r.message || [];

				let graph_items = results.slice(0, 10);

				me.$graph_area.show().empty();
				let args = {
					data: {
						datasets: [
							{
								values: graph_items.map(d=>d.value)
							}
						],
						labels: graph_items.map(d=>d.name)
					},
					colors: ['light-green'],
					format_tooltip_x: d=>d[me.options.selected_filter_item],
					type: 'bar',
					height: 140
				};
				new frappeChart.Chart('.leaderboard-graph', args);

				notify(me, r, $container);
			}
		});
	},


	
	get_leaderboard_data: function (me, res, $container) {
		if (res && res.message) {
			me.message = null;
			$container.find(".leaderboard-list").html(me.render_list_view(res.message));
		} else {
			me.$graph_area.hide();
			me.message = __("No items found.");
			$container.find(".leaderboard-list").html(me.render_list_view());
		}
	},

	render_list_view: function (items = []) {
		var me = this;

		var html =
			`${me.render_message()}
			 <div class="result" style="${me.message ? "display:none;" : ""}">
			 	${me.render_result(items)}
			 </div>`;

		return $(html);
	},

	render_result: function (items) {
		var me = this;

		var html =
			`${me.render_list_header()}
			${me.render_list_result(items)}`;

		return html;
	},

	render_list_header: function () {
		var me = this;
		const _selected_filter = me.options.selected_filter
			.map(i => frappe.model.unscrub(i));
		const fields = ['name', me.options.selected_filter_item];

		const html =
			`<div class="list-headers">
				<div class="list-item list-item--head" data-list-renderer="${"List"}">
					${
					fields.map(filter => {
							const col = frappe.model.unscrub(filter);
							return (
								`<div class="leaderboard-item list-item_content ellipsis text-muted list-item__content--flex-2
									header-btn-base
									${(col && _selected_filter.indexOf(col) !== -1) ? "text-right" : ""}">
									<span class="list-col-title ellipsis">
										${col}
									</span>
								</div>`);
						}).join("")
					}
				</div>
			</div>`;
		return html;
	},

	render_list_result: function (items) {
		var me = this;

		let _html = items.map((item, index) => {
			const $value = $(me.get_item_html(item));

			let item_class = "";
			if(index == 0) {
				item_class = "first";
			} else if (index == 1) {
				item_class = "second";
			} else if(index == 2) {
				item_class = "third";
			}
			const $item_container = $(`<div class="list-item-container  ${item_class}">`).append($value);
			return $item_container[0].outerHTML;
		}).join("");

		let html =
			`<div class="result-list">
				<div class="list-items">
					${_html}
				</div>
			</div>`;

		return html;
	},

	render_message: function () {
		var me = this;

		let html =
			`<div class="no-result text-center" style="${me.message ? "" : "display:none;"}">
				<div class="msg-box no-border">
					<p>No Item found</p>
				</div>
			</div>`;

		return html;
	},

	get_item_html: function (item) {
		var me = this;
		const company = me.options.selected_company;
		const currency = frappe.get_doc(":Company", company).default_currency;
		const fields = ['name','value'];

		const html =
			`<div class="list-item">
				${
			fields.map(col => {
					let val = item[col];
					if(col=="name") {
						var formatted_value = `<a class="grey list-id ellipsis"
							href="#Form/${me.options.selected_doctype}/${item["name"]}"> ${val} </a>`
					} else {
						var formatted_value = `<span class="text-muted ellipsis">
							${(me.options.selected_filter_item.indexOf('qty') == -1) ? format_currency(val, currency) : val}</span>`
					}

					return (
						`<div class="list-item_content ellipsis list-item__content--flex-2
							${(col == "value") ? "text-right" : ""}">
							${formatted_value}
						</div>`);
					}).join("")
				}
			</div>`;

		return html;
	},
	*/
	get_sidebar_item: function(item) {
		return $(`<li class="strong module-sidebar-item">
			<a class="module-link">
			<span doctype-value="${item}">${ __(item) }</span></a>
		</li>`);
	}
});

