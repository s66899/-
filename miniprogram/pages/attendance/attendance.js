const api = require('../../utils/api')
Page({
  data: {
    date: '', day: '星期一', dayIndex: 0,
    days: ['星期一','星期二','星期三','星期四','星期五','星期六','星期日'],
    slots: [], slotIndex: 0, slot: '',
    attStudents: [], selectedCount: 0
  },
  onShow() {
    const now = new Date()
    this.setData({ date: now.toISOString().split('T')[0] })
    const dayIdx = [7,1,2,3,4,5,6][now.getDay()] || 1
    this.setData({ dayIndex: dayIdx, day: this.data.days[dayIdx] })
    this.loadSlots()
  },
  onDateChange(e) { this.setData({ date: e.detail.value }) },
  onDayChange(e) {
    const idx = e.detail.value
    this.setData({ dayIndex: idx, day: this.data.days[idx] })
    this.loadSlots()
  },
  async loadSlots() {
    try {
      const settings = await api.get('/api/settings')
      const slots = settings.time_slots[this.data.day] || []
      this.setData({ slots, slotIndex: 0, slot: slots[0] || '' })
    } catch(e) { console.error(e) }
  },
  onSlotChange(e) {
    const idx = e.detail.value
    this.setData({ slotIndex: idx, slot: this.data.slots[idx] })
  },
  async loadStudents() {
    const { day, slot } = this.data
    if (!slot) return wx.showToast({ title: '请选择时间段', icon: 'none' })
    try {
      const [schedules, students] = await Promise.all([
        api.get(`/api/schedules?day=${day}`),
        api.get('/api/students')
      ])
      const studentMap = {}
      students.forEach(s => studentMap[s.id] = s)
      const matched = schedules.filter(s => s.time_slot === slot)
      const attStudents = matched.map(s => {
        const stu = studentMap[s.student_id] || {}
        return { id: s.id, studentId: s.student_id, name: stu.name||'未知', coach: s.coach||'', remaining_hours: stu.remaining_hours||0, selected: false }
      })
      this.setData({ attStudents, selectedCount: 0 })
    } catch(e) { console.error(e) }
  },
  toggleSelect(e) {
    const idx = e.currentTarget.dataset.index
    const key = `attStudents[${idx}].selected`
    const val = !this.data.attStudents[idx].selected
    this.setData({ [key]: val })
    this.setData({ selectedCount: this.data.attStudents.filter(s => s.selected).length })
  },
  async takeAttendance() {
    const selected = this.data.attStudents.filter(s => s.selected)
    if (selected.length === 0) return wx.showToast({ title: '请选择学员', icon: 'none' })
    wx.showModal({
      title: '确认消课',
      content: `确定对 ${selected.length} 名学员消课？`,
      success: async (res) => {
        if (!res.confirm) return
        wx.showLoading({ title: '消课中...' })
        for (const s of selected) {
          await api.post('/api/attendance', { student_id: s.studentId, hours_used: 1, date: this.data.date })
        }
        wx.hideLoading()
        wx.showToast({ title: '消课成功' })
        this.loadStudents()
      }
    })
  }
})
