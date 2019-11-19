var watchExampleVM = new Vue({
    el: '#app',
    data: {
      drugText: null,
      predictions: 'Awaiting input...',
      moleculeId: ''
    },
    created: function () {
      document.addEventListener('DOMContentLoaded', function() {
        M.FormSelect.init(document.querySelectorAll('select'));
      })
    },
    watch: {
      drugText: function () {
        this.moleculeId = ''
        this.predictions = 'Waiting for you to stop typing...'
        this.getPredictions()
      },
      drugSection: function () {
        this.moleculeId = ''
        this.predictions = 'Waiting for you to stop typing...'
        this.getPredictions()
      }
    },
    methods: {
      getPredictions: _.debounce(function () {
        if (!this.drugText) {
          this.predictions = 'Awaiting input...'
          return
        }

        var vm = this
        this.moleculeId = ''
        axios.post('/drug-predict/', {
          drug_text: this.drugText,
          ui: true
        })
          .then(function (response) {
            vm.predictions = response.data.predictions.slice(0, 10);
            vm.moleculeId = response.data.moleculeId ? response.data.moleculeId : ''
          })
          .catch(function (error) {
            vm.predictions = 'Error! Could not reach the API. ' + error
          })
        }, 500) // This is the number of milliseconds we wait for the user to stop typing.
    }
  })
