const api = require('../../utils/api')

Page({
  data: { stats: {} },
  onShow() { this.loadStats() },
  async loadStats() {
    try {
      const stats = await api.get('/api/stats')
      this.setData({ stats })
    } catch(e) { console.error(e) }
  },
  goToStudents() { wx.navigateTo({ url: '/pages/students/students' }) },
  goToSchedule() { wx.navigateTo({ url: '/pages/schedule/schedule' }) },
  goToAttendance() { wx.navigateTo({ url: '/pages/attendance/attendance' }) },
  goToStats() { wx.navigateTo({ url: '/pages/stats/stats' }) }
})
