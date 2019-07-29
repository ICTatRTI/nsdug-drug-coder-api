var watchExampleVM = new Vue({
    el: '#app',
    data: {
      courseNumber: '',
      courseTitle: '',
      predictions: 'Awaiting input...',
    },
    watch: {
      // whenever question changes, this function will run
      courseNumber: function (newDrugSection, oldDrugSection) {
        this.predictions = 'Waiting for you to stop typing...'
        this.getPredictions()
      },
      courseTitle: function (newDrugText, oldDrugText) {
        this.predictions = 'Waiting for you to stop typing...'
        this.getPredictions()
      }
    },
    methods: {
      getPredictions: _.debounce(
        function () {
          if (this.courseNumber === '' || this.courseTitle === '') {
            this.predictions = 'Awaiting input...'
            return
          }
          var vm = this
          axios.post('http://localhost:23432/drug-predict/',{
            drug_section: this.drugSection,
            drug_text: this.drugText
          })
            .then(function (response) {
              vm.predictions = response.data.predictions.slice(0, 10);
            })
            .catch(function (error) {
              vm.predictions = 'Error! Could not reach the API. ' + error
            })
        },
        // This is the number of milliseconds we wait for the
        // user to stop typing.
        500
      )
    }
  })
  