const api = require('../../utils/api')
Page({
  data: { currentDay: '星期一', days: ['星期一','星期二','星期三','星期四','星期五','星期六','星期日'], scheduleData: [] },
  onShow() { this.loadData() },
  switchDay(e) { this.setData({ currentDay: e.currentTarget.dataset.day }, () => this.loadData()) },
  async loadData() {
    try {
      const [schedules, settings, students] = await Promise.all([
        api.get(`/api/schedules?day=${this.data.currentDay}`),
        api.get('/api/settings'),
        api.get('/api/students')
      ])
      const slots = settings.time_slots[this.data.currentDay] || []
      const coaches = settings.coaches || []
      const maxPerCoach = settings.max_students_per_coach || 6
      const studentMap = {}
      students.forEach(s => studentMap[s.id] = s)
      const scheduleData = slots.map(slot => {
        const slotSchedules = schedules.filter(s => s.time_slot === slot)
        const coachData = coaches.map(c => {
          const matched = slotSchedules.filter(s => s.coach === c)
          const studentNames = matched.map(s => (studentMap[s.student_id]||{}).name || '未知')
          return { name: c, students: studentNames, count: studentNames.length, max: maxPerCoach }
        })
        return { time: slot, coaches: coachData }
      })
      this.setData({ scheduleData })
    } catch(e) { console.error(e) }
  }
})
