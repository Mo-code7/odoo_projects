odoo.define('livestock_management.dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;

    var _t = core._t;

    var LivestockDashboard = AbstractAction.extend({
        template: 'LivestockDashboard',
        
        events: {
            'click .quick-action-btn': '_onQuickActionClick',
            'click .stat-card': '_onStatCardClick',
            'click .activity-item': '_onActivityClick',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.stats = {};
            this.activities = [];
        },

        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._loadDashboardData();
            });
        },

        _loadDashboardData: function () {
            var self = this;
            return rpc.query({
                model: 'livestock.animal',
                method: 'get_dashboard_stats',
                args: [],
            }).then(function (stats) {
                self.stats = stats;
            }).then(function () {
                return rpc.query({
                    model: 'livestock.animal',
                    method: 'get_recent_activities',
                    args: [],
                });
            }).then(function (activities) {
                self.activities = activities;
            });
        },

        _onQuickActionClick: function (ev) {
            ev.preventDefault();
            var action = $(ev.currentTarget).data('action');
            
            switch (action) {
                case 'create_animal':
                    this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'livestock.animal',
                        view_mode: 'form',
                        target: 'new',
                        context: {},
                    });
                    break;
                case 'view_animals':
                    this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'livestock.animal',
                        view_mode: 'list,form,kanban',
                        context: {},
                    });
                    break;
                case 'view_alive':
                    this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'livestock.animal',
                        view_mode: 'list,form',
                        domain: [('status', '=', 'alive')],
                        context: {},
                    });
                    break;
                case 'view_sick':
                    this.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'livestock.animal',
                        view_mode: 'list,form',
                        domain: [('status', '=', 'sick')],
                        context: {},
                    });
                    break;
            }
        },

        _onStatCardClick: function (ev) {
            ev.preventDefault();
            var status = $(ev.currentTarget).data('status');
            
            if (status) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'livestock.animal',
                    view_mode: 'list,form',
                    domain: [('status', '=', status)],
                    context: {},
                });
            }
        },

        _onActivityClick: function (ev) {
            ev.preventDefault();
            var animalId = $(ev.currentTarget).data('animal-id');
            
            if (animalId) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'livestock.animal',
                    view_mode: 'form',
                    res_id: animalId,
                    target: 'current',
                });
            }
        },

        _updateStats: function () {
            var self = this;
            return rpc.query({
                model: 'livestock.animal',
                method: 'get_dashboard_stats',
                args: [],
            }).then(function (stats) {
                self.stats = stats;
                self._renderStats();
            });
        },

        _renderStats: function () {
            var $statsContainer = this.$('.dashboard-stats');
            $statsContainer.empty();
            
            var stats = [
                {
                    title: _t('إجمالي الحيوانات'),
                    value: this.stats.total_animals || 0,
                    icon: 'fa-cow',
                    color: 'primary',
                    status: null
                },
                {
                    title: _t('حيوانات حية'),
                    value: this.stats.alive_animals || 0,
                    icon: 'fa-heart',
                    color: 'success',
                    status: 'alive'
                },
                {
                    title: _t('حيوانات مريضة'),
                    value: this.stats.sick_animals || 0,
                    icon: 'fa-medical-kit',
                    color: 'warning',
                    status: 'sick'
                },
                {
                    title: _t('حيوانات نافقة'),
                    value: this.stats.dead_animals || 0,
                    icon: 'fa-times-circle',
                    color: 'danger',
                    status: 'dead'
                }
            ];
            
            stats.forEach(function (stat) {
                var $statCard = $(QWeb.render('LivestockStatCard', {
                    stat: stat
                }));
                $statsContainer.append($statCard);
            });
        },

        _renderActivities: function () {
            var $activitiesContainer = this.$('.activity-list');
            $activitiesContainer.empty();
            
            if (this.activities.length === 0) {
                $activitiesContainer.append($('<div class="text-muted text-center p-3">').text(_t('لا توجد أنشطة حديثة')));
                return;
            }
            
            this.activities.forEach(function (activity) {
                var $activityItem = $(QWeb.render('LivestockActivityItem', {
                    activity: activity
                }));
                $activitiesContainer.append($activityItem);
            });
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderStats();
                self._renderActivities();
                
                // تحديث البيانات كل 5 دقائق
                setInterval(function () {
                    self._updateStats();
                }, 300000);
            });
        },
    });

    core.action_registry.add('livestock_dashboard', LivestockDashboard);

    return LivestockDashboard;
});

// إضافة قوالب QWeb
odoo.define('livestock_management.dashboard_templates', function (require) {
    "use strict";

    var QWeb = require('web.core').qweb;

    QWeb.add_template(`
        <t t-name="LivestockDashboard">
            <div class="o_livestock_dashboard">
                <div class="dashboard-header">
                    <h1>🐄 لوحة تحكم إدارة المواشي</h1>
                    <div class="dashboard-actions">
                        <button class="btn btn-primary quick-action-btn" data-action="create_animal">
                            <i class="fa fa-plus"></i>
                            إضافة حيوان جديد
                        </button>
                        <button class="btn btn-secondary quick-action-btn" data-action="view_animals">
                            <i class="fa fa-list"></i>
                            عرض جميع الحيوانات
                        </button>
                    </div>
                </div>
                
                <div class="dashboard-stats">
                    <!-- سيتم ملؤها بواسطة JavaScript -->
                </div>
                
                <div class="dashboard-content">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="dashboard-activities">
                                <h3>📊 الأنشطة الحديثة</h3>
                                <div class="activity-list">
                                    <!-- سيتم ملؤها بواسطة JavaScript -->
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="dashboard-quick-actions">
                                <h3>⚡ إجراءات سريعة</h3>
                                <div class="quick-actions-grid">
                                    <a href="#" class="quick-action-btn" data-action="view_alive">
                                        <i class="fa fa-heart"></i>
                                        <span>الحيوانات الحية</span>
                                    </a>
                                    <a href="#" class="quick-action-btn" data-action="view_sick">
                                        <i class="fa fa-medical-kit"></i>
                                        <span>الحيوانات المريضة</span>
                                    </a>
                                    <a href="#" class="quick-action-btn" data-action="create_animal">
                                        <i class="fa fa-plus"></i>
                                        <span>إضافة حيوان</span>
                                    </a>
                                    <a href="#" class="quick-action-btn" data-action="view_animals">
                                        <i class="fa fa-list"></i>
                                        <span>جميع الحيوانات</span>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </t>
    `);

    QWeb.add_template(`
        <t t-name="LivestockStatCard">
            <div class="stat-card" t-att-data-status="stat.status">
                <div class="stat-icon">
                    <i t-att-class="'fa ' + stat.icon"></i>
                </div>
                <div class="stat-content">
                    <h3><t t-esc="stat.title"/></h3>
                    <div class="stat-value"><t t-esc="stat.value"/></div>
                </div>
            </div>
        </t>
    `);

    QWeb.add_template(`
        <t t-name="LivestockActivityItem">
            <div class="activity-item" t-att-data-animal-id="activity.animal_id">
                <div class="activity-icon">
                    <i class="fa fa-info"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-text"><t t-esc="activity.text"/></div>
                    <div class="activity-time"><t t-esc="activity.time"/></div>
                </div>
            </div>
        </t>
    `);
});
