const api = require('../../utils/api')
Page({
  data: { stats: {} },
  onShow() { this.loadStats() },
  async loadStats() {
    try {
      const stats = await api.get('/api/stats')
      this.setData({ stats })
    } catch(e) { console.error(e) }
  }
})
