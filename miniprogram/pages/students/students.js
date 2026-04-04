const api = require('../../utils/api')
Page({
  data: { students: [], searchText: '', statusFilter: '' },
  onShow() { this.loadStudents() },
  async loadStudents() {
    const { searchText, statusFilter } = this.data
    let url = '/api/students?'
    if (statusFilter) url += `status=${statusFilter}&`
    if (searchText) url += `search=${searchText}`
    try {
      const students = await api.get(url)
      this.setData({ students })
    } catch(e) { console.error(e) }
  },
  onSearch(e) { this.setData({ searchText: e.detail.value }, () => this.loadStudents()) },
  setFilter(e) { this.setData({ statusFilter: e.currentTarget.dataset.status }, () => this.loadStudents()) },
  showDetail(e) {
    const s = e.currentTarget.dataset.item
    wx.showModal({
      title: s.name,
      content: `电话: ${s.phone||'-'}\n等级: ${s.level||'-'}\n教练: ${s.coach||'-'}\n购买课时: ${s.purchased_hours}\n赠送课时: ${s.bonus_hours}\n剩余课时: ${s.remaining_hours}\n备注: ${s.note||'-'}`,
      showCancel: false
    })
  }
})
