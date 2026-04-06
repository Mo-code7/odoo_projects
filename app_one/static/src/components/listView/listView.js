/* @odoo-module */

import { Component, useState, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks"
import { FormView } from "@app_one/components/formView/formView"

export class ListViewAction extends Component {
        static template = "app_one.ListView";
        static components = { FormView }
        setup(){
          this.state=useState({
                  'records':[]
          });
          this.orm=useService("orm");
          this.rpc=useService("rpc");
          this.loadRecords();   
          this.intervalId=setInterval(()=>{this.loadRecords()}, 3000);
          this.onRecordCreated = this.onRecordCreated.bind(this);
          onWillUnmount(() =>{clearInterval(this.intervalId)});           
        };
        // async loadRecords(){
        //   const result = await this.orm.searchRead("property",[],[]);
        //   console.log(result);      
        //   this.state.records=result;
        // };

        async loadRecords(){
          const result = await this.rpc("/web/dataset/call_kw",{
            model:'property',
            method:'search_read',
            args:[[]],
            kwargs:{fields:['id','name','postcode','date_available']},
          })
          this.state.records = result;  
        };

        async createRecords(){
          await this.rpc("/web/dataset/call_kw",{
            model: 'property',
            method: 'create',
            args: [{
              name: 'Property for moaz',
              postcode: '722002',
              date_available: '2026-2-25'
            }],
            kwargs: {},
          })
          this.loadRecords();
        };

        async deleteRecords(recordId){
          await this.rpc("/web/dataset/call_kw",{
            model: 'property',
            method: 'unlink',
            args: [recordId],
            kwargs: {},
          })
          this.loadRecords();
        };

        tooggleCreateForm(){
          console.log('Toogle create form view ')
          this.state.showCreateForm = !this.state.showCreateForm;
          console.log(this.state.showCreateForm);
        };

        onRecordCreated(){
          this.loadRecords();
          this.state.showCreateForm = false;
        };
}


registry.category("actions").add("app_one.action_list_view",ListViewAction);





